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

    'pipeline',

    'jepostule.auth.apps.AuthConfig',
    'jepostule.embed',
    'jepostule.pipeline.apps.PipelineConfig',
    'jepostule.queue',
    'jepostule.security',
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
                'jepostule.context_processors.template_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Default database points to local docker container
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('POSTGRES_HOST', '127.0.0.1'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'NAME': os.environ.get('POSTGRES_DB', 'jepostule'),
        'USER': os.environ.get('POSTGRES_USER', 'jepostule'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'mdp'),
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

# Static assets management
STATIC_URL = '/static/'
STATIC_ROOT = '/tmp/jepostule/static'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'jepostule', 'static'),
]
STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
)
# https://django-pipeline.readthedocs.io/en/latest/configuration.html
PIPELINE = {
    'JAVASCRIPT': {
        'common': {
            'source_filenames': (
                'js/common/localStorage.js',
            ),
            'output_filename': 'js/common.js',
        },
        'answer': {
            'source_filenames': (
                'vendor/jquery.min.js',
                'vendor/jquery.datetimepicker.full.js',
            ),
            'output_filename': 'js/answer.js',
        },
        'polyfill': {
            'source_filenames': (
                'js/polyfill/forEach.js',
                'js/polyfill/event.js',
            ),
            'output_filename': 'js/polyfill.js',
        }
    },
    'STYLESHEETS': {
        'answer': {
            'source_filenames': (
                'css/jepostule-base.css',
                'css/pipeline-form.css',
                'vendor/jquery.datetimepicker.min.css',
            ),
            'output_filename': 'css/answer.css',
        },
        'embed': {
            'source_filenames': (
                'css/jepostule-base.css',
                'css/embed-iframe.css',
            ),
            'output_filename': 'css/embed.css',
        },
    },
}

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

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_DB = os.environ.get('REDIS_DB', '0')

JEPOSTULE_BASE_URL = os.environ.get('JEPOSTULE_BASE_URL', 'http://127.0.0.1:8000')
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_SENDING_MODULE = 'jepostule.email.backends.django'
JEPOSTULE_NO_REPLY = 'contact@jepostule.labonneboite.pole-emploi.fr'
PLATFORM_ATTRIBUTES = {}
ATTACHMENTS_MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 Mb
BLACKLIST_DURATION_SECONDS = 30 * 24 * 3600
MAILJET_API_BASE_URL = "https://api.mailjet.com/v3.1"
MAILJET_API_KEY = "setme"
MAILJET_API_SECRET = "setme"

# Analytics
GOOGLE_ANALYTICS_TRACKING_ID = None
HOTJAR_SITE_ID = None

# For secure callback url, assign a random string value
EVENT_CALLBACK_SECRET = None

QUEUE_PRODUCER = 'jepostule.queue.handlers.franz.KafkaProducer'
QUEUE_CONSUMER = 'jepostule.queue.handlers.franz.KafkaConsumer'
QUEUE_RUN_ASYNC = True
KAFKA_BOOTSTRAP_SERVERS = [os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')]

TEST_RUNNER = 'jepostule.tests.runner.JePostuleRunner'
