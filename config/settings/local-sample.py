from .base import * # pylint: disable=unused-wildcard-import

DEBUG = False
ALLOWED_HOSTS = [
    'jepostule.pole-emploi.fr',
    'localhost',
]
STATIC_ROOT = '/var/www/jepostule/static'

# SECRET_KEY = 'setme'
DATABASES['default']['HOST'] = 'postgres'
# DATABASES['default']['PASSWORD'] = 'setme'

REDIS_HOST = 'redis'

KAFKA_BOOTSTRAP_SERVERS = ['kafka:9092']

# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'setme'
# EMAIL_PORT = 0
# EMAIL_HOST_USER = 'setme'
# EMAIL_HOST_PASSWORD = 'setme'

# import sentry_sdk
# sentry_sdk.init(
    # "https://set@sentry.io/me",
    # environment="production"
# )
