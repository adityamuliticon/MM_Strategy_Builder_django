import redis
from config import Config

_client = None


def get_redis():
    global _client
    if _client is None:
        _client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True,
        )
    return _client
