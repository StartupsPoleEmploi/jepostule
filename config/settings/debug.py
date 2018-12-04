from .base import *# pylint: disable=unused-wildcard-import

INSTALLED_APPS.append('debug_toolbar')
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
INTERNAL_IPS = ['127.0.0.1']
