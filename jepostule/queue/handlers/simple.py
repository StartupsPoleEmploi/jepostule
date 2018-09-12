from collections import defaultdict

from . import base


TASKS = defaultdict(list)


class SimpleProducer(base.BaseProducer):

    def send(self, topic, value, key=None):
        TASKS[topic].append(value)


class SimpleConsumer(base.BaseConsumer):

    def __iter__(self):
        while TASKS[self.topic]:
            yield TASKS[self.topic].pop(0)
