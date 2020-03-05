from .base import * # pylint: disable=unused-wildcard-import


REDIS_DB = 1
PIPELINE['PIPELINE_ENABLED'] = False
STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'

LOGGING['handlers'] = {
    'console': {
        'class': 'logging.StreamHandler',
        'formatter': 'simple',
        'level': 'CRITICAL',
    },
}
LOGGING['loggers'] = {
    'root': {
        'handlers': ['console'],
        'level': 'CRITICAL',
    },
}

# Disable Kafka in tests
QUEUE_PRODUCER = 'jepostule.queue.handlers.simple.SimpleProducer'
QUEUE_CONSUMER = 'jepostule.queue.handlers.simple.SimpleConsumer'
KAFKA_BOOTSTRAP_SERVERS = []
