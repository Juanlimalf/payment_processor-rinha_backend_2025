import redis

from config import settings


class RedisClient:
    __slots__ = ("redis_client",)

    def __init__(self, host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0):
        pool = redis.ConnectionPool(host=host, port=port, db=db, max_connections=100)
        self.redis_client = redis.Redis(connection_pool=pool)

    def get_client(self):
        return self.redis_client


redis_client = RedisClient().get_client()
