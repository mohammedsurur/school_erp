# config/settings/railway.py
# Railway-specific settings.
# Railway auto-sets DATABASE_URL and PORT environment variables.

from .base import *
import os
import dj_database_url

# ─────────────────────────────────────────────
#  Core
# ─────────────────────────────────────────────

DEBUG      = False
SECRET_KEY = os.environ['SECRET_KEY']   # set in Railway dashboard

ALLOWED_HOSTS = [
    '.railway.app',           # all Railway subdomains
    '.up.railway.app',        # Railway deployment URLs
    os.environ.get('RAILWAY_STATIC_URL', ''),
    os.environ.get('CUSTOM_DOMAIN', ''),  # your custom domain if any
]
# Remove empty strings
ALLOWED_HOSTS = [h for h in ALLOWED_HOSTS if h]

# ─────────────────────────────────────────────
#  Database — Railway auto-provides DATABASE_URL
# ─────────────────────────────────────────────

DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,
    )
}

# ─────────────────────────────────────────────
#  Static files — WhiteNoise serves them
# ─────────────────────────────────────────────

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─────────────────────────────────────────────
#  Security — HTTPS enforced by Railway
# ─────────────────────────────────────────────

SECURE_PROXY_SSL_HEADER       = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT            = True
SESSION_COOKIE_SECURE          = True
CSRF_COOKIE_SECURE             = True
SECURE_HSTS_SECONDS            = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF    = True
X_FRAME_OPTIONS                = 'DENY'

CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://*.up.railway.app',
]
# Add your custom domain if set
_custom = os.environ.get('CUSTOM_DOMAIN', '')
if _custom:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_custom}')

# ─────────────────────────────────────────────
#  CORS
# ─────────────────────────────────────────────

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS   = [
    'https://*.railway.app',
    'https://*.up.railway.app',
]
if _custom:
    CORS_ALLOWED_ORIGINS.append(f'https://{_custom}')

# ─────────────────────────────────────────────
#  Email — console fallback (add SMTP later)
# ─────────────────────────────────────────────

EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST          = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@school.com')

# ─────────────────────────────────────────────
#  Caching — Railway Redis (if added)
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
    # Fallback to local memory cache if no Redis
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# ─────────────────────────────────────────────
#  Logging — stdout so Railway dashboard shows it
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
        'django.security': {
            'handlers':  ['console'],
            'level':     'WARNING',
            'propagate': False,
        },
    },
}

# ─────────────────────────────────────────────
#  DRF — JSON only in production
# ─────────────────────────────────────────────

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
]

# ─────────────────────────────────────────────
#  Admin URL — obscure it
# ─────────────────────────────────────────────

ADMIN_URL = os.environ.get('ADMIN_URL', 'admin/')
