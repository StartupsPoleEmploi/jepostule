from time import sleep

from django.test import TestCase

from jepostule.pipeline import ratelimits
from jepostule.kvstore import redis


class RateLimitTests(TestCase):

    def setUp(self):
        redis().flushall()

    def test_single_rate_limit(self):
        class TestLimiter(ratelimits.BaseLimiter):
            LIMITS = [
                (1, 10)
            ]

        delay1 = TestLimiter.delay('key')
        TestLimiter.add('key')
        delay2 = TestLimiter.delay('key')

        self.assertEqual(0, delay1)
        self.assertLess(9, delay2)
        self.assertLess(delay2, 10)

    def test_multiple_rate_limits(self):
        class TestLimiter(ratelimits.BaseLimiter):
            LIMITS = [
                (1, 10),
                (1, 60),
                (2, 120),
            ]
        delay1 = TestLimiter.delay('key')
        TestLimiter.add('key')
        delay2 = TestLimiter.delay('key')
        TestLimiter.add('key')
        delay3 = TestLimiter.delay('key')

        self.assertEqual(0, delay1)
        self.assertLess(59, delay2)
        self.assertLess(delay2, 60)
        self.assertLess(119, delay3)
        self.assertLess(delay3, 120)


    def test_flushing(self):
        class TestLimiter(ratelimits.BaseLimiter):
            LIMITS = [
                (1, 1),
            ]
        TestLimiter.add('key', 1)
        TestLimiter.add('key', 2)
        events1 = TestLimiter.events('key', 0, 2)
        TestLimiter.flush('key', 1.5)
        events2 = TestLimiter.events('key', 0, 2)

        self.assertEqual([(b'1', 1.0), (b'2', 2.0)], events1)
        self.assertEqual([(b'2', 2.0)], events2)

    def test_keys_expire(self):
        class TestLimiter(ratelimits.BaseLimiter):
            LIMITS = [
                (1, 1),
            ]
        TestLimiter.add('key', 1)
        self.assertEqual([(b'1', 1.0)], TestLimiter.events('key', 0, 2))
        sleep(1)
        self.assertEqual([], TestLimiter.events('key', 0, 2))
