import logging
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any

from livekit import rtc
from livekit.agents import Agent, ModelSettings, RunContext, function_tool, llm, stt
from livekit.agents.beta.tools import EndCallTool
from livekit.agents.llm import ChatContext

if TYPE_CHECKING:
    from .agent import BengaliAgent, EnglishAgent, HindiAgent

logger = logging.getLogger(__name__)


class BaseAgent(Agent):
    """
    Extended Agent class with streaming capabilities for LLM, STT, and TTS.
    Optimized for ultra-fast streaming with minimal latency and async TTS.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize streaming agent with session tracking.

        Args:
            publish_interval: Publish to frontend every N tokens (default: 1 for max speed)
        """
        existing_tools = kwargs.get('tools', []) or []
        if not isinstance(existing_tools, list):
            existing_tools = list(existing_tools)

        end_call_tool = EndCallTool(
            extra_description="End the call only when the user explicitly requests to end the conversation or says goodbye.",
            delete_room=True,
            end_instructions="Thank the user for using Travel Planner. Say a friendly goodbye message."
        )
        all_tools = existing_tools + list(end_call_tool.tools)

        kwargs['tools'] = all_tools
        super().__init__(*args, **kwargs)
        self.language = "en"
        self._conversation_summary: str = ""
        self._max_ctx_items = 8
        self._language_agent_map: dict[str, Any] = {}

    @function_tool()
    async def transfer_to_language(self, context: RunContext, language_code: str) -> tuple[Agent, str]:
        """
        Transfer the conversation to a different language agent.

        Args:
            context: The run context
            language_code: Target language code ('en' for English, 'hi' for Hindi, 'bn' for Bengali)

        Returns:
            Tuple of (new_agent, message) to trigger handoff
        """
        language_code = language_code.lower().strip()

        valid_languages = {
            'en': ('English', EnglishAgent),
            'hi': ('Hindi', HindiAgent),
            'bn': ('Bengali', BengaliAgent)
        }

        if language_code not in valid_languages:
            return self, f"Language '{language_code}' is not supported. Available languages: English (en), Hindi (hi), Bengali (bn)"

        language_name, agent_class = valid_languages[language_code]
        new_agent = agent_class(chat_ctx=self.chat_ctx.copy())

        logger.info(f"Language transferring from {self.language} to {language_code}")
        self.language = language_code

        message = f"Perfect! I'm switching to {language_name}. I'll continue assisting you in {language_name}. आपकी मदद करने के लिए तैयार हूँ। আপনার সেবায় নিয়োজিত আছি।"
        return new_agent, message

    @property
    def conversation_summary(self) -> str:
        return self._conversation_summary

    async def on_enter(self):
        await self.session.generate_reply()

    async def stt_node(
        self, audio: AsyncIterable[rtc.AudioFrame], model_settings: ModelSettings
    ) -> AsyncIterable[stt.SpeechEvent | str]:
        async def filtered_audio():
            async for frame in audio:
                yield frame

        async for event in Agent.default.stt_node(
            self, filtered_audio(), model_settings
        ):
            if event.alternatives:
                self.language = event.alternatives[0].language or self.language
            yield event

    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        model_settings: ModelSettings,
    ) -> AsyncIterable[llm.ChatChunk]:
        truncated_ctx = chat_ctx.truncate(max_items=self._max_ctx_items)
        await self._summarize_truncated_messages(chat_ctx, truncated_ctx)

        async for chunk in Agent.default.llm_node(
            self, chat_ctx=truncated_ctx, model_settings=model_settings, tools=self.tools
        ):
            yield chunk

    async def _summarize_truncated_messages(
        self, full_ctx: ChatContext, truncated_ctx: ChatContext
    ) -> None:
        if len(full_ctx.items) <= self._max_ctx_items:
            return

        truncated_count = len(full_ctx.items) - len(truncated_ctx.items)
        if truncated_count <= 0:
            return

        summary_ctx = ChatContext()
        summary_ctx.add_message(
            role="system",
            content="Summarize the following conversation briefly, capturing key points and context:",
        )

        for item in full_ctx.items[:truncated_count]:
            if item.type == "message" and item.role in ("user", "assistant"):
                text = (item.text_content or "").strip()
                if text:
                    summary_ctx.add_message(role="user", content=f"{item.role}: {text}")

        if len(summary_ctx.items) <= 1:
            return

        try:
            llm_instance = self.session.llm
            if llm_instance and isinstance(llm_instance, llm.LLM):
                response = await llm_instance.chat(chat_ctx=summary_ctx).collect()
                self._conversation_summary = (
                    response.text.strip() if response.text else ""
                )
        except Exception:
            pass

    async def tts_node(
        self, text: AsyncIterable[str], model_settings: ModelSettings
    ) -> AsyncIterable[rtc.AudioFrame]:
        async for frame in Agent.default.tts_node(self, text, model_settings):
            yield frame





