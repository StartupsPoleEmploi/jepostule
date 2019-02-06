from django.test import TestCase

from jepostule.kvstore import redis


class CacheTestCase(TestCase):

    def setUp(self):
        redis().flushall()
        super().setUp()
