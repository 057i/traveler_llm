"""

"""
import redis
from loguru import logger
from typing import Optional
from config.settings import settings


class RedisClient:

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._connect()

    def _connect(self):
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            self.client.ping()
            logger.info(f"Redis连接成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self.client = None

    def get(self, key: str) -> Optional[str]:
        try:
            if self.client:
                return self.client.get(key)
            return None
        except Exception as e:
            logger.error(f"Redis GET失败: {e}")
            return None

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        try:
            if self.client:
                self.client.set(key, value, ex=ex)
                return True
            return False
        except Exception as e:
            logger.error(f"Redis SET失败: {e}")
            return False

    def delete(self, *keys: str) -> int:
        try:
            if self.client:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis DELETE失败: {e}")
            return 0

    def lpush(self, key: str, *values: str) -> int:
        try:
            if self.client:
                return self.client.lpush(key, *values)
            return 0
        except Exception as e:
            logger.error(f"Redis LPUSH失败: {e}")
            return 0

    def rpush(self, key: str, *values: str) -> int:
        try:
            if self.client:
                return self.client.rpush(key, *values)
            return 0
        except Exception as e:
            logger.error(f"Redis RPUSH失败: {e}")
            return 0

    def lrange(self, key: str, start: int, end: int) -> list:
        try:
            if self.client:
                return self.client.lrange(key, start, end)
            return []
        except Exception as e:
            logger.error(f"Redis LRANGE失败: {e}")
            return []

    def llen(self, key: str) -> int:
        try:
            if self.client:
                return self.client.llen(key)
            return 0
        except Exception as e:
            logger.error(f"Redis LLEN失败: {e}")
            return 0

    def expire(self, key: str, time: int) -> bool:
        try:
            if self.client:
                return self.client.expire(key, time)
            return False
        except Exception as e:
            logger.error(f"Redis EXPIRE失败: {e}")
            return False

    def lrem(self, key: str, count: int, value: str) -> int:
        try:
            if self.client:
                return self.client.lrem(key, count, value)
            return 0
        except Exception as e:
            logger.error(f"Redis LREM失败: {e}")
            return 0

    def publish(self, channel: str, message: str) -> int:
        """
        发布消息到Redis Pub/Sub频道

        Args:
            channel: 频道名称
            message: 消息内容

        Returns:
            接收到消息的订阅者数量
        """
        try:
            if self.client:
                return self.client.publish(channel, message)
            return 0
        except Exception as e:
            logger.error(f"Redis PUBLISH失败: {e}")
            return 0


_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client