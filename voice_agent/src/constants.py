import os

from dotenv import load_dotenv

load_dotenv()


class RedisConfig:
    host = os.getenv("REDIS_HOST", "redis-12980.crce281.ap-south-1-3.ec2.cloud.redislabs.com")
    port = int(os.getenv("REDIS_PORT", "12980"))
    password = os.getenv("REDIS_PASSWORD", "zo9Qk9rTjWYv19ARvEXTtPcDXmf0ARkN")
    ssl = True

    @property
    def url(self) -> str:
        return f"rediss://:{self.password}@{self.host}:{self.port}"


class LiveKitConfig:
    livekit_api_key = os.getenv("LIVEKIT_API_KEY")
    livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")


class MongoConfig:
    mongodb_uri = os.getenv("MONGODB_URI")
    mongodb_name = os.getenv("MONGODB_NAME", "voice_agent")
    mongodb_user_collection = os.getenv("MONGODB_USER_COLLECTION", "users")
    mongodb_conversation_collection = os.getenv("MONGODB_CONVERSATION_COLLECTION", "conversations")


class Credentials:
    livekit = LiveKitConfig()
    mongo = MongoConfig()
    redis = RedisConfig()
