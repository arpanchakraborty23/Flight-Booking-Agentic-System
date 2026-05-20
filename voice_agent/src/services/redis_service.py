import json
import logging
from typing import Any, Optional

import redis

logger = logging.getLogger(__name__)


class RedisService:
    def __init__(self, host: str, port: int, password: str, ssl: bool = True):
        self.client = redis.Redis(
            host=host,
            port=port,
            password=password,
            ssl=ssl,
            decode_responses=True
        )
        self._test_connection()

    def _test_connection(self):
        try:
            self.client.ping()
            logger.info("✅ Redis connected successfully")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise

    def _get_session_key(self, session_id: str) -> str:
        return f"session:{session_id}"

    def _get_conversation_key(self, session_id: str) -> str:
        return f"conversation:{session_id}"

    def store_message(self, session_id: str, message: dict[str, Any]):
        key = self._get_conversation_key(session_id)
        self.client.rpush(key, json.dumps(message))
        self.client.expire(key, 86400)

    def get_conversation(self, session_id: str) -> list[dict[str, Any]]:
        key = self._get_conversation_key(session_id)
        data = self.client.lrange(key, 0, -1)
        return [json.loads(item) for item in data]

    def set_session_data(self, session_id: str, data: dict[str, Any]):
        key = self._get_session_key(session_id)
        self.client.hset(key, mapping=data)
        self.client.expire(key, 86400)

    def get_session_data(self, session_id: str) -> Optional[dict[str, Any]]:
        key = self._get_session_key(session_id)
        data = self.client.hgetall(key)
        return data if data else None

    def delete_session(self, session_id: str):
        self.client.delete(self._get_session_key(session_id))
        self.client.delete(self._get_conversation_key(session_id))
        logger.info(f"🧹 Deleted Redis keys for session {session_id}")

    def flush_conversation(self, session_id: str) -> list[dict[str, Any]]:
        conversation = self.get_conversation(session_id)
        self.delete_session(session_id)
        return conversation
