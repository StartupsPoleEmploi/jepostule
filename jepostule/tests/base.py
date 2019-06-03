from django.test import TestCase

from jepostule.kvstore import redis
from jepostule.queue.handlers.simple import reset_tasks


class CacheTestCase(TestCase):

    def setUp(self):
        redis().flushall()
        super().setUp()


class PipelineCacheTestCase(CacheTestCase):

    def setUp(self):
        reset_tasks()
        super().setUp()


class PipelineTestCase(TestCase):

    def setUp(self):
        reset_tasks()
        super().setUp()