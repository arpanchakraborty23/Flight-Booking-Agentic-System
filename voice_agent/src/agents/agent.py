from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

from livekit.agents import ChatContext, inference
from livekit.agents.llm import FallbackAdapter as LLMFallBack
from livekit.agents.stt import FallbackAdapter as STTFallBack
from livekit.agents.tts import FallbackAdapter as TTSFallBack
from livekit.plugins import deepgram, elevenlabs, sarvam, silero

from src.prompts.bengali import TRAVEL_PLANNER_SYSTEM_PROMPT_BENGALI
from src.prompts.english import TRAVEL_PLANNER_SYSTEM_PROMPT
from src.prompts.hindi import TRAVEL_PLANNER_SYSTEM_PROMPT_HINDI

from . import BaseAgent


class EnglishAgent(BaseAgent):
    def __init__(self, *, vad: silero.VAD = None, chat_ctx: ChatContext = None) -> None:
        self._vad = vad
        super().__init__(
            instructions=TRAVEL_PLANNER_SYSTEM_PROMPT,
            stt=STTFallBack(
                stt=[
                    sarvam.STT(language="en-IN",model="saaras:v2.5",api_key=os.getenv("SARVAM_API_KEY") or ""),
                    inference.STT(model="assemblyai/universal-streaming"),
                    deepgram.STT(model="conversationalai",language="en-IN",enable_diarization=True,),
                ]
            ),
            llm=LLMFallBack(
                llm=[
                    sarvam.LLM(model="sarvam-30b", api_key=os.getenv("SARVAM_API_KEY") or ""),
                    inference.LLM(model="openai/gpt-4.1-mini")
                ]
            ),
            tts=TTSFallBack(
                tts=[
                    elevenlabs.TTS(api_key=os.getenv("ELEVENLABS_API_KEY") or "",model="eleven_multilingual_v2",sync_alignment=True,enable_ssml_parsing=True),
                    inference.TTS(model="elevenlabs/eleven_multilingual_v2"),
                    sarvam.TTS(
                        target_language_code="en-IN",
                        api_key=os.getenv("SARVAM_API_KEY") or ""
                    ),
                ]
            ),
            chat_ctx=chat_ctx,
            vad=vad,
        )


class HindiAgent(BaseAgent):
    def __init__(self, *, vad: silero.VAD = None, chat_ctx: ChatContext = None) -> None:
        self._vad = vad
        super().__init__(
            instructions=TRAVEL_PLANNER_SYSTEM_PROMPT_HINDI,
            stt=STTFallBack(
                stt=[
                    sarvam.STT(language="hi-IN", model="saaras:v2.5", api_key=os.getenv("SARVAM_API_KEY") or ""),
                    inference.STT(model="assemblyai/universal-streaming"),
                    deepgram.STT(
                        model="conversationalai",
                        language="hi-IN",
                        enable_diarization=True,
                    ),
                ]
            ),
            llm=LLMFallBack(
                llm=[
                    sarvam.LLM(model="sarvam-30b", api_key=os.getenv("SARVAM_API_KEY") or ""),
                    inference.LLM(model="openai/gpt-4.1-mini"),
                ]
            ),
            tts=TTSFallBack(
                tts=[
                    elevenlabs.TTS(api_key=os.getenv("ELEVENLABS_API_KEY") or "", model="eleven_multilingual_v2", sync_alignment=True, enable_ssml_parsing=True),
                    inference.TTS(model="elevenlabs/eleven_multilingual_v2"),
                    sarvam.TTS(
                        target_language_code="hi-IN",
                        api_key=os.getenv("SARVAM_API_KEY") or ""
                    ),
                ]
            ),
            chat_ctx=chat_ctx,
            vad=vad,
        )


class BengaliAgent(BaseAgent):
    def __init__(self, *, vad: silero.VAD = None, chat_ctx: ChatContext = None) -> None:
        self._vad = vad
        super().__init__(
            instructions=TRAVEL_PLANNER_SYSTEM_PROMPT_BENGALI,
            stt=STTFallBack(
                stt=[
                    sarvam.STT(language="bn-IN", model="saaras:v2.5", api_key=os.getenv("SARVAM_API_KEY") or ""),
                    inference.STT(model="assemblyai/universal-streaming"),
                    deepgram.STT(
                        model="conversationalai",
                        language="bn-IN",
                        enable_diarization=True,
                    ),
                ]
            ),
            llm=LLMFallBack(
                llm=[
                    sarvam.LLM(model="sarvam-30b", api_key=os.getenv("SARVAM_API_KEY") or ""),
                    inference.LLM(model="openai/gpt-4.1-mini"),
                ]
            ),
            tts=TTSFallBack(
                tts=[
                    elevenlabs.TTS(api_key=os.getenv("ELEVENLABS_API_KEY") or "", model="eleven_multilingual_v2", sync_alignment=True, enable_ssml_parsing=True),
                    inference.TTS(model="elevenlabs/eleven_multilingual_v2"),
                    sarvam.TTS(
                        target_language_code="bn-IN",
                        api_key=os.getenv("SARVAM_API_KEY") or ""
                    ),
                ]
            ),
            chat_ctx=chat_ctx,
            vad=vad,
        )
