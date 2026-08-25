# config/settings/railway.py  — FIXED

from .base import *
import os
import dj_database_url

# ─────────────────────────────────────────────
#  Core
# ─────────────────────────────────────────────

DEBUG = False

# FIX: use .get() with a dummy fallback for build phase
# At runtime Railway injects the real SECRET_KEY
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'build-phase-temporary-key-replaced-at-runtime'
)

# Your Railway domain from image 4
ALLOWED_HOSTS = [
    'schoolerp.up.railway.app',
    '.railway.app',
    '.up.railway.app',
    os.environ.get('RAILWAY_PUBLIC_DOMAIN', ''),
    os.environ.get('CUSTOM_DOMAIN', ''),
    os.environ.get('ALLOWED_HOSTS', ''),
]
ALLOWED_HOSTS = [h for h in ALLOWED_HOSTS if h]

# ─────────────────────────────────────────────
#  Database
# ─────────────────────────────────────────────

# Only configure DB if DATABASE_URL is available (not during build)
_db_url = os.environ.get('DATABASE_URL', '')
if _db_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=_db_url,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
else:
    # Fallback during build phase — no DB needed for collectstatic
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME':   '/tmp/build.sqlite3',
        }
    }

# ─────────────────────────────────────────────
#  Static files — WhiteNoise
# ─────────────────────────────────────────────

# Insert WhiteNoise after SecurityMiddleware
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = (
    'whitenoise.storage.CompressedManifestStaticFilesStorage'
)
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─────────────────────────────────────────────
#  Security
# ─────────────────────────────────────────────

SECURE_PROXY_SSL_HEADER        = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT            = True
SESSION_COOKIE_SECURE          = True
CSRF_COOKIE_SECURE             = True
SECURE_HSTS_SECONDS            = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF    = True
X_FRAME_OPTIONS                = 'DENY'

CSRF_TRUSTED_ORIGINS = [
    'https://schoolerp.up.railway.app',
    'https://*.railway.app',
    'https://*.up.railway.app',
]
_custom = os.environ.get('CUSTOM_DOMAIN', '')
if _custom:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_custom}')

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS   = [
    'https://schoolerp.up.railway.app',
    'https://*.railway.app',
]

# ─────────────────────────────────────────────
#  Email
# ─────────────────────────────────────────────

EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST          = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.environ.get(
    'DEFAULT_FROM_EMAIL', 'noreply@schoolerp.up.railway.app'
)

# ─────────────────────────────────────────────
#  Caching
# ─────────────────────────────────────────────

_redis_url = os.environ.get('REDIS_URL', '')
if _redis_url:
    CACHES = {
        'default': {
            'BACKEND':  'django.core.cache.backends.redis.RedisCache',
            'LOCATION': _redis_url,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# ─────────────────────────────────────────────
#  Logging — stdout for Railway dashboard
# ─────────────────────────────────────────────

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'railway': {
            'format': '{levelname} {asctime} {module} {message}',
            'style':  '{',
        },
    },
    'handlers': {
        'console': {
            'class':     'logging.StreamHandler',
            'formatter': 'railway',
        },
    },
    'root': {
        'handlers': ['console'],
        'level':    'INFO',
    },
    'loggers': {
        'django': {
            'handlers':  ['console'],
            'level':     'INFO',
            'propagate': False,
        },
    },
}

# ─────────────────────────────────────────────
#  DRF
# ─────────────────────────────────────────────

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
]

# ─────────────────────────────────────────────
#  Admin URL
# ─────────────────────────────────────────────

ADMIN_URL = os.environ.get('ADMIN_URL', 'admin/')