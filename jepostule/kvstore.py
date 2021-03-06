from redis import ConnectionPool
from redis import Redis as RedisClient

from django.conf import settings


class Redis:
    CONNECTION_POOL = None

    @classmethod
    def client(cls):
        if cls.CONNECTION_POOL is None:
            cls.CONNECTION_POOL = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB
            )
        return RedisClient(connection_pool=cls.CONNECTION_POOL)

def redis():
    """
    Return a redis client.
    """
    return Redis.client()
