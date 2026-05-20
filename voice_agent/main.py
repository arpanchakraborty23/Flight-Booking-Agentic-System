import logging
import os
from typing import Optional

from livekit import agents, api, rtc
from livekit.agents import (
    AgentServer,
    AgentSession,
    JobProcess,
    MetricsCollectedEvent,
    SessionUsageUpdatedEvent,
    metrics,
    room_io,
)
from livekit.agents.metrics import (
    EOUMetrics,
    InterruptionMetrics,
    LLMMetrics,
    STTMetrics,
    TTSMetrics,
    VADMetrics,
)
from livekit.plugins import noise_cancellation, silero

from src.constants import Credentials
from src.services import SessionManager
from src.voice_agent import BengaliAgent, EnglishAgent, HindiAgent, MetricsCollector

livekit_config = Credentials.livekit

logger = logging.getLogger(__name__)

server = AgentServer(
    api_key=livekit_config.livekit_api_key,
    api_secret=livekit_config.livekit_api_secret,
    ws_url=livekit_config.livekit_url
)


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def my_agent(ctx: agents.JobContext):
    ctx.log_context_fields = {"room_name": ctx.room.name}
    await ctx.connect()

    participant = await ctx.room.get_participant()
    if not participant:
        logger.error("No participant found in room")
        return

    participant_context = {
        "identity": participant.identity or "",
        "name": participant.name or "",
        "session_id": ctx.room.name,
    }
    logger.info("Participant context: %s", participant_context)

    agent = EnglishAgent()
    session_manager = SessionManager()
    metrics_collector = MetricsCollector()

    session = AgentSession(
        vad=silero.VAD.load(),
        turn_handling={
            "endpointing": {
                "mode": "dynamic",
                "min_delay": 0.5,
                "max_delay": 1.5,
            },
            "interruption": {
                "mode": "adaptive",
                "min_duration": 0.4,
                "resume_false_interruption": True,
            },
            "preemptive_generation": {
                "enabled": True,
                "preemptive_tts": True,
            },
        },
    )

    session_manager.start(session_id=ctx.room.name, participant_context=participant_context)


    await session.start(
        room=ctx.room,
        agent=agent,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony() if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP else noise_cancellation.BVC(),
            ),
        ),
    )

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        m = ev.metrics

        if isinstance(m, STTMetrics):
            metrics_collector.collect_stt(m)
        elif isinstance(m, VADMetrics):
            metrics_collector.collect_vad(m)
        elif isinstance(m, EOUMetrics):
            metrics_collector.collect_eou(m)
        elif isinstance(m, LLMMetrics):
            metrics_collector.collect_llm(m)
        elif isinstance(m, TTSMetrics):
            metrics_collector.collect_tts(m)
        elif isinstance(m, InterruptionMetrics):
            metrics_collector.collect_interruption(m)

    @session.on("session_usage_updated")
    def _on_session_usage_updated(ev: SessionUsageUpdatedEvent):
        metrics_collector.update_session_usage(ev)

    # Event handler for conversation items
    @session.on("conversation_item_added")
    def on_conversation_item(event):
        """Handle conversation items (covers both user and agent messages)."""
        try:
            item = event.item
            if hasattr(item, 'content') and item.content:
                speaker = "USER" if hasattr(item, 'role') and item.role == 'user' else "AGENT"
                log_entry = {
                    "role": speaker.lower(),
                    "message": item.content,
                    "speaker": speaker
                }
                session_manager.session_log(log_entry)

            if event.item.metrics:
                latency_data = {
                    "latency": getattr(event.item.metrics, 'latency', 0.0),
                    "audio_duration": getattr(event.item.metrics, 'audio_duration', 0.0),
                }
                session_manager.add_turn_latency(event.item.role, latency_data)

        except Exception as e:
            logger.error(f"Error logging conversation item: {e}")

    # Handle session shutdown and cleanup
    async def end_handler():
        """Handle session end and perform cleanup."""
        try:
            session_manager.update_metrics(metrics_collector.get_summary())
            session_manager.end_session()

            logger.info(f"Session for room {ctx.room.name} ended and cleaned up.")
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")

    ctx.add_shutdown_callback(end_handler)

if __name__ == "__main__":
    agents.cli.run_app(server)
