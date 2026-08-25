# config/settings/dev.py
# Local development overrides.
# Usage: set DJANGO_SETTINGS_MODULE=config.settings.dev

from .base import *
import os

# ─────────────────────────────────────────────
#  Core
# ─────────────────────────────────────────────

DEBUG       = True
SECRET_KEY  = 'dev-insecure-key-change-in-production-xj3!k9$m2q'

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# ─────────────────────────────────────────────
#  Database (PostgreSQL for dev parity)
# ─────────────────────────────────────────────

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.environ.get('DB_NAME', 'school_erp'),
        'USER':     os.environ.get('DB_USER', 'school_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST':     os.environ.get('DB_HOST', 'localhost'),
        'PORT':     os.environ.get('DB_PORT', '5432'),
    }
}

# ─────────────────────────────────────────────
#  Email — print to console in dev
# ─────────────────────────────────────────────

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ─────────────────────────────────────────────
#  CORS — allow all in dev
# ─────────────────────────────────────────────

CORS_ALLOW_ALL_ORIGINS = True

# ─────────────────────────────────────────────
#  Django Debug Toolbar (optional)
# ─────────────────────────────────────────────

try:
    import debug_toolbar
    INSTALLED_APPS  += ['debug_toolbar']
    MIDDLEWARE       = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
    INTERNAL_IPS     = ['127.0.0.1']
except ImportError:
    pass

# ─────────────────────────────────────────────
#  Logging — show SQL in dev
# ─────────────────────────────────────────────

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level':    'INFO',
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level':    'WARNING',   # set to DEBUG to see all SQL
            'propagate': False,
        },
    },
}

# ─────────────────────────────────────────────
#  DRF — browsable API in dev
# ─────────────────────────────────────────────

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',  # nice HTML view
]