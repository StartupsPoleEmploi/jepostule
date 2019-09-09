"""
Settings for end-to-end tests.
See jepostule/tests/end_to_end
"""
import os
import copy
from distutils.util import strtobool

from .test import * # pylint: disable=unused-wildcard-import


EMAIL_DELIVERY_SERVICE = 'mailjet'
MAILJET_API_KEY = os.environ.get('MAILJET_API_KEY', "set_me")
MAILJET_API_SECRET = os.environ.get('MAILJET_API_SECRET', "set_me")
MAILJET_API_BASE_URL = "https://api.mailjet.com/v3.1"
QUEUE_PRODUCER = 'jepostule.queue.handlers.franz.KafkaProducer'
QUEUE_CONSUMER = 'jepostule.queue.handlers.franz.KafkaConsumer'
KAFKA_BOOTSTRAP_SERVERS = [os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')]

BACKDOOR_CANDIDATE_EMAIL = os.environ.get('BACKDOOR_CANDIDATE_EMAIL', 'set_me')
BACKDOOR_EMPLOYER_EMAIL = os.environ.get('BACKDOOR_EMPLOYER_EMAIL', 'set_me')

MEMO_API_URL = 'https://memo.beta.pole-emploi.fr/rest/api/v1'
MEMO_API_SECRET = os.environ.get('MEMO_API_SECRET', 'set_me')
MEMO_API_VERIFY_SSL = False

# Run Selenium in headless mode, ie do not open a window to show browser interaction.
RUN_HEADLESS = bool(strtobool(os.environ.get('RUN_HEADLESS', 'True')))

DATABASES['default'].update({
    'NAME': 'test_jepostule',
})

DATABASES['TEST'] = copy.deepcopy(DATABASES['default'])


LOGGING['handlers'] = {
    'console': {
        'class': 'logging.StreamHandler',
        'formatter': 'simple',
        'level': 'INFO',
    },
}
LOGGING['loggers'] = {
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

TEST_RUNNER = 'jepostule.tests.runner.NoDbRunner'
