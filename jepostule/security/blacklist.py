from time import time

from jepostule.kvstore import redis
from django.conf import settings


class Details:

    def __init__(self, email):
        self.key = key(email)
        reason = redis().get(self.key)
        self.reason = reason.decode() if reason is not None else None

    @property
    def is_blacklisted(self):
        return self.reason is not None

    def expire_in(self):
        """
        Return:
            ttl (None/float): the delay in seconds before the email is removed
            from the blacklist. None if the key is not blacklisted.
        """
        ttl = redis().pttl(self.key)
        if ttl == -2:
            return None
        return ttl / 1000

def add(email, reason='', timestamp=None):
    duration = expire_in(timestamp)
    if duration > 0:
        redis().set(key(email), reason.encode())
        redis().expire(key(email), duration)

def remove(email):
    redis().delete(key(email))

def is_blacklisted(email):
    return Details(email).is_blacklisted

def details(email):
    return Details(email)

def key(email):
    return ("blacklist:{}".format(email)).encode()

def expire_in(start_timestamp=None):
    now = time()
    start_timestamp = start_timestamp or now
    return int(start_timestamp + settings.BLACKLIST_DURATION_SECONDS - now)
