from .base import *

DEBUG = True

# Development-specific settings
INSTALLED_APPS += [
    'debug_toolbar',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

INTERNAL_IPS = ['127.0.0.1']

MEDIA_ROOT = BASE_DIR / "media"
