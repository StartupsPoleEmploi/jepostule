# Base settings are optimized for local development.
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SECRET_KEY = 'CHANGEME'

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'jepostule.auth.apps.AuthConfig',
    'jepostule.embed',
    'jepostule.pipeline',
    'jepostule.queue',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'jepostule', 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Default database points to local docker container
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('POSTGRESQL_HOST', '127.0.0.1'),
        'PORT': os.environ.get('POSTGRESQL_PORT', '5432'),
        'NAME': os.environ.get('POSTGRESQL_DB', 'jepostule'),
        'USER': os.environ.get('POSTGRESQL_USER', 'jepostule'),
        'PASSWORD': os.environ.get('POSTGRESQL_PASSWORD', 'mdp'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'jepostule', 'static'),
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[{asctime}]{levelname}:{name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'INFO',
        },
    },
    'loggers': {
        'root': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'jepostule': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

############ JePostule-specific settings

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
JEPOSTULE_NO_REPLY = 'no-reply@jepostule.pole-emploi.fr'
ATTACHMENTS_MAX_SIZE_BYTES = 10*1024*1024 # 10 Mb

# This dict contains pairs of client ID/secret.
# Values can be generated with the following shell command:
# python -c "import random, string; print(''.join([random.choice(string.ascii_lowercase + string.digits) for _ in range(12)]))"
JEPOSTULE_CLIENTS = {
    'democlientid': 'democlientsecret',
}

QUEUE_PRODUCER = 'jepostule.queue.handlers.franz.KafkaProducer'
QUEUE_CONSUMER = 'jepostule.queue.handlers.franz.KafkaConsumer'
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']

TEST_RUNNER = 'jepostule.tests.runner.JePostuleRunner'
