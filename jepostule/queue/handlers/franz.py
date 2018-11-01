import logging

from django.conf import settings
import kafka

from . import base


logger = logging.getLogger(__name__)


class KafkaProducer(base.BaseProducer):

    def send(self, topic, value, key=None):
        producer = kafka.KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        )
        producer.send(
            topic, value=value, key=key,
        ).add_errback(self.on_send_error)
        producer.flush()

    @staticmethod
    def on_send_error(e):
        raise e


class KafkaConsumer(base.BaseConsumer):
    """
    Consume messages from a Kafka topic.
    """

    GROUP_ID = 'jepostule'
    TIMEOUT_MS = 3000

    def __init__(self, topic):
        super().__init__(topic)
        self.kafka_consumer = kafka.KafkaConsumer(
            self.topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=self.GROUP_ID,
            enable_auto_commit=False,
            consumer_timeout_ms=self.TIMEOUT_MS,
        )

    def __iter__(self):
        while True:
            for message in self.kafka_consumer:
                self.kafka_consumer.commit()
                yield message.value
            yield None
