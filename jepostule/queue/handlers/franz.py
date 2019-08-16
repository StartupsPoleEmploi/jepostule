import logging
import time

from django.conf import settings
import kafka
from kafka.errors import GroupLoadInProgressError
from kafka.admin.client import KafkaAdminClient

from . import base
from . import exceptions


logger = logging.getLogger(__name__)


class KafkaProducer(base.BaseProducer):

    def send(self, topic, value, key=None):
        producer = kafka.KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            max_request_size=11534336,
        )
        result = producer.send(
            topic, value=value, key=key,
        ).add_errback(self.on_send_error)
        producer.flush()
        if result.failed():
            raise exceptions.ProduceError(topic, value, key)

    @staticmethod
    def on_send_error(e):
        # Don't raise an exception here, because it's going to be caught
        # We need to log an error in addition to an exception. This
        # is because exception stacktraces that contain attachments
        # are very large, and they may not reach sentry.
        logger.error("An error occurred in the Kafka producer: %s", e)
        logger.exception(e)


class KafkaConsumer(base.BaseConsumer):
    """
    Consume messages from a Kafka topic.
    """

    GROUP_ID = 'jepostule'
    TIMEOUT_MS = 3000

    def __init__(self, topic):
        super().__init__(topic)

        while True:
            try:
                # Make sure Kafka is reachable before we create a new consumer.
                client = KafkaAdminClient(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
                client.list_consumer_groups()
                break
            except (ValueError, TypeError, GroupLoadInProgressError, ):
                logger.info('Waiting for Kafka to be up...')
                time.sleep(2)

        self.kafka_consumer = kafka.KafkaConsumer(
            self.topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=self.GROUP_ID,
            enable_auto_commit=True,
            consumer_timeout_ms=self.TIMEOUT_MS,
            auto_offset_reset='earliest',
        )
        logger.info(f'Kafka consumer created for topic {self.topic}')


    def __iter__(self):
        logger.info(f"{[message.value for message in self.kafka_consumer]}")
        while True:
            for message in self.kafka_consumer:
                # Envoie l'offset actuel à Kafka pour marquer le message comme lu.
                self.kafka_consumer.commit()
                # exécute la fonction qui est stockée dans le message.
                yield message.value
            yield None

