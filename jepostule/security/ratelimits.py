from time import time
from jepostule.kvstore import redis


class BaseLimiter:
    """
    Set rate limits and compute corresponding delays,

    Rate limits are set in the LIMITS variable: it is a list of (X, Y) tuples
    that are read as "maximum of X events every Y seconds".
    """
    LIMITS = []
    KEY_PREFIX = "baselimiter"

    @classmethod
    def delay(cls, key):
        """
        Compute the time delay necessary before an event can happen for this key again.
        Basically, what we do here is a time sliding window to compute the number
        of events that have occurred for this key in the last seconds. We use
        the redis sorted sets to compute the number of events.

        Return:
            delay (float): time delay in seconds that we should wait before the
            rate limits no longer apply.
        """
        max_delay = 0
        now = time()
        cls.flush_unneeded(key, now)
        for max_count, timedelta in cls.LIMITS:
            events = cls.events(key, now - timedelta, now)
            if len(events) >= max_count:
                # makes total sense
                delay = events[len(events) - max_count][1] + timedelta - now
                max_delay = max(delay, max_delay)
        return max_delay

    @classmethod
    def add(cls, key, score=None):
        """
        Add an event for key. This event will be used to apply rate limits.
        """
        score = score or time()
        client = redis()
        client.zadd(cls.key(key), {score: score})
        client.expire(cls.key(key), cls.max_delay())

    @classmethod
    def flush_unneeded(cls, key, now):
        cls.flush(0, now - cls.max_delay())

    @classmethod
    def flush(cls, key, score=None):
        score = score if score is not None else time()
        redis().zremrangebyscore(cls.key(key), 0, score)

    @classmethod
    def events(cls, key, minscore, maxscore):
        return redis().zrangebyscore(
            cls.key(key), minscore, maxscore, withscores=True,
        )

    @classmethod
    def key(cls, k):
        return 'ratelimit:{}:{}'.format(cls.KEY_PREFIX, k)

    @classmethod
    def max_delay(cls):
        return max([t[1] for t in cls.LIMITS]) if cls.LIMITS else 0


class Sender(BaseLimiter):
    LIMITS = [
        (1, 1),
        (3, 60),
        (60, 3600),
    ]
    KEY_PREFIX = "sender"
