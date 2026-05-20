import logging
from datetime import datetime
from typing import Any, Optional

from src.constants import Credentials

from .mongo_service import MongoServices
from .redis_service import RedisService

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self):
        redis_config = Credentials.redis
        self.redis = RedisService(
            host=redis_config.host,
            port=redis_config.port,
            password=redis_config.password,
            ssl=redis_config.ssl
        )
        self._session_id: Optional[str] = None
        self._participant_context: Optional[dict[str, Any]] = None
        self._start_time: Optional[datetime] = None
        self._metrics_data: dict[str, Any] = {}
        self._turn_latencies: list[dict[str, Any]] = []
        self._user_state: str = "connected"
        self._call_ended_by_user: bool = False

    def start(self, session_id: str, participant_context: dict[str, Any]):
        self._session_id = session_id
        self._participant_context = participant_context
        self._start_time = datetime.now()
        self._metrics_data = {}
        self._turn_latencies = []
        self._user_state = "connected"
        self._call_ended_by_user = False

        user_info = {
            "identity": participant_context.get("identity", ""),
            "name": participant_context.get("name", ""),
            "language": participant_context.get("language", "en"),
            "session_id": session_id,
            "state": self._user_state,
        }

        self.redis.set_session_data(session_id, {
            "user_info": str(user_info),
            "started_at": self._start_time.isoformat(),
            "state": self._user_state
        })
        logger.info(f"📝 Session started: {session_id}")

    def session_log(self, log_entry: dict[str, Any]):
        if not self._session_id:
            logger.warning("No active session to log to")
            return
        self.redis.store_message(self._session_id, log_entry)

    def update_metrics(self, metrics: dict[str, Any]):
        self._metrics_data = metrics

    def add_turn_latency(self, role: str, latency_data: dict[str, Any]):
        self._turn_latencies.append({
            "role": role,
            "latency": latency_data.get("latency", 0.0),
            "audio_duration": latency_data.get("audio_duration", 0.0),
            "timestamp": datetime.now().isoformat()
        })

    def set_user_state(self, state: str):
        self._user_state = state
        if self._session_id:
            self.redis.set_session_data(self._session_id, {"state": state})
        logger.info(f"👤 User state: {state}")

    def set_call_ended_by_user(self, ended: bool = True):
        self._call_ended_by_user = ended

    def end_session(self, reason: str = "normal") -> dict[str, Any]:
        if not self._session_id:
            logger.warning("No active session to end")
            return {}

        end_time = datetime.now()
        conversation = self.redis.flush_conversation(self._session_id)

        duration_seconds = (end_time - self._start_time).total_seconds() if self._start_time else 0
        total_latency = sum(t.get("latency", 0) for t in self._turn_latencies)
        avg_turn_latency = total_latency / len(self._turn_latencies) if self._turn_latencies else 0

        session_data = {
            "session_id": self._session_id,
            "user_info": {
                "identity": self._participant_context.get("identity", "") if self._participant_context else "",
                "name": self._participant_context.get("name", "") if self._participant_context else "",
                "language": self._participant_context.get("language", "en") if self._participant_context else "en",
            },
            "session_timing": {
                "start_time": self._start_time.isoformat() if self._start_time else None,
                "end_time": end_time.isoformat(),
                "duration_seconds": round(duration_seconds, 2),
            },
            "user_state": {
                "final_state": self._user_state,
                "ended_by_user": self._call_ended_by_user,
                "end_reason": reason,
            },
            "conversation": {
                "total_messages": len(conversation),
                "messages": conversation,
            },
            "metrics_summary": {
                "stt": self._metrics_data.get("stt", {}),
                "llm": self._metrics_data.get("llm", {}),
                "tts": self._metrics_data.get("tts", {}),
                "vad": self._metrics_data.get("vad", {}),
                "eou": self._metrics_data.get("eou", {}),
                "interruption": self._metrics_data.get("interruption", {}),
            },
            "latency_summary": {
                "total_turn_latency": round(total_latency, 2),
                "avg_turn_latency": round(avg_turn_latency, 2),
                "total_turns": len(self._turn_latencies),
            }
        }

        self._save_to_mongodb(session_data)
        logger.info(f"📴 Session ended: {self._session_id}, reason: {reason}")

        self._session_id = None
        self._participant_context = None
        self._start_time = None
        self._metrics_data = {}
        self._turn_latencies = []
        self._user_state = "disconnected"
        return session_data

    def _save_to_mongodb(self, session_data: dict[str, Any]):
        try:
            mongo_config = Credentials.mongo
            mongo = MongoServices(
                url=mongo_config.mongodb_uri or "",
                db=mongo_config.mongodb_name or "",
                collection=mongo_config.mongodb_conversation_collection or ""
            )
            mongo.insert_one(session_data)
            logger.info(f"💾 Saved session {session_data['session_id']} to MongoDB")
        except Exception as e:
            logger.error(f"❌ Failed to save session to MongoDB: {e}")
