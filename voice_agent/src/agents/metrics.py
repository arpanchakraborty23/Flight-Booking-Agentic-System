import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class STTMetricsData:
    total_requests: int = 0
    total_duration: float = 0.0
    total_latency: float = 0.0
    avg_latency: float = 0.0
    errors: int = 0


@dataclass
class VADMetricsData:
    total_segments: int = 0
    total_speech_duration: float = 0.0
    speech_to_text_ratio: float = 0.0


@dataclass
class EOUMetricsData:
    total_eou: int = 0
    avg_eou_latency: float = 0.0


@dataclass
class LLMMetricsData:
    total_requests: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_duration: float = 0.0
    avg_latency: float = 0.0
    total_cost: float = 0.0


@dataclass
class TTSMetricsData:
    total_requests: int = 0
    total_characters: int = 0
    total_duration: float = 0.0
    avg_latency: float = 0.0


@dataclass
class InterruptionMetricsData:
    total_interruptions: int = 0
    total_interruption_duration: float = 0.0
    interruption_rate: float = 0.0


class MetricsCollector:
    def __init__(self):
        self._stt = STTMetricsData()
        self._vad = VADMetricsData()
        self._eou = EOUMetricsData()
        self._llm = LLMMetricsData()
        self._tts = TTSMetricsData()
        self._interruption = InterruptionMetricsData()
        self._turn_latencies: list[dict[str, Any]] = []
        self._session_usage: dict[str, Any] = {}

    def collect_stt(self, m: Any):
        self._stt.total_requests += 1
        self._stt.total_duration += getattr(m, 'audio_duration', 0.0)
        self._stt.total_latency += getattr(m, 'latency', 0.0)
        if self._stt.total_requests > 0:
            self._stt.avg_latency = self._stt.total_latency / self._stt.total_requests
        logger.debug(f"STT metrics: requests={self._stt.total_requests}, avg_latency={self._stt.avg_latency:.2f}ms")

    def collect_vad(self, m: Any):
        self._vad.total_segments += 1
        speech_duration = getattr(m, 'speech_duration', 0.0)
        self._vad.total_speech_duration += speech_duration
        if self._vad.total_segments > 0:
            self._vad.speech_to_text_ratio = self._vad.total_speech_duration / max(1, self._vad.total_segments)

    def collect_eou(self, m: Any):
        self._eou.total_eou += 1
        eou_latency = getattr(m, 'latency', 0.0)
        current_avg = self._eou.avg_eou_latency
        self._eou.avg_eou_latency = (current_avg * (self._eou.total_eou - 1) + eou_latency) / self._eou.total_eou

    def collect_llm(self, m: Any):
        self._llm.total_requests += 1
        self._llm.total_prompt_tokens += getattr(m, 'prompt_tokens', 0)
        self._llm.total_completion_tokens += getattr(m, 'completion_tokens', 0)
        self._llm.total_duration += getattr(m, 'duration', 0.0)
        if self._llm.total_requests > 0:
            self._llm.avg_latency = self._llm.total_duration / self._llm.total_requests

    def collect_tts(self, m: Any):
        self._tts.total_requests += 1
        self._tts.total_characters += getattr(m, 'characters', 0)
        self._tts.total_duration += getattr(m, 'audio_duration', 0.0)
        if self._tts.total_requests > 0:
            self._tts.avg_latency = (self._tts.avg_latency * (self._tts.total_requests - 1) + getattr(m, 'latency', 0.0)) / self._tts.total_requests

    def collect_interruption(self, m: Any):
        self._interruption.total_interruptions += 1
        self._interruption.total_interruption_duration += getattr(m, 'duration', 0.0)

    def add_turn_latency(self, role: str, metrics: Any):
        latency_data = {
            "role": role,
            "timestamp": datetime.now().isoformat(),
            "latency": getattr(metrics, 'latency', 0.0),
            "audio_duration": getattr(metrics, 'audio_duration', 0.0),
        }
        self._turn_latencies.append(latency_data)

    def update_session_usage(self, ev: Any):
        self._session_usage = {
            "prompt_tokens": getattr(ev, 'prompt_tokens', 0),
            "completion_tokens": getattr(ev, 'completion_tokens', 0),
            "total_tokens": getattr(ev, 'total_tokens', 0),
            "entities": getattr(ev, 'entities', 0),
        }

    def get_summary(self) -> dict[str, Any]:
        return {
            "stt": self._stt.__dict__,
            "vad": self._vad.__dict__,
            "eou": self._eou.__dict__,
            "llm": self._llm.__dict__,
            "tts": self._tts.__dict__,
            "interruption": self._interruption.__dict__,
            "turn_latencies": self._turn_latencies,
            "session_usage": self._session_usage,
        }

    def reset(self):
        self._stt = STTMetricsData()
        self._vad = VADMetricsData()
        self._eou = EOUMetricsData()
        self._llm = LLMMetricsData()
        self._tts = TTSMetricsData()
        self._interruption = InterruptionMetricsData()
        self._turn_latencies = []
        self._session_usage = {}
