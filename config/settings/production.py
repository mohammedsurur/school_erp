
from .base import *
import os

# ─────────────────────────────────────────────
#  Core
# ─────────────────────────────────────────────

DEBUG      = False
SECRET_KEY = os.environ['SECRET_KEY']    # crash loudly if missing

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'school.example.com').split(',')

# ─────────────────────────────────────────────
#  Database — PostgreSQL with SSL
# ─────────────────────────────────────────────

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.environ['DB_NAME'],
        'USER':     os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST':     os.environ.get('DB_HOST', 'localhost'),
        'PORT':     os.environ.get('DB_PORT', '5432'),
        'OPTIONS':  {'sslmode': 'require'},
        'CONN_MAX_AGE': 60,   # persistent connections
    }
}

# ─────────────────────────────────────────────
#  Security headers
# ─────────────────────────────────────────────

# HTTPS
SECURE_SSL_REDIRECT              = True
SECURE_PROXY_SSL_HEADER          = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS — tell browsers to always use HTTPS (1 year)
SECURE_HSTS_SECONDS              = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS   = True
SECURE_HSTS_PRELOAD              = True

# Cookies
SESSION_COOKIE_SECURE            = True
SESSION_COOKIE_HTTPONLY          = True
SESSION_COOKIE_SAMESITE          = 'Lax'
SESSION_COOKIE_AGE               = 28800          # 8 hours
CSRF_COOKIE_SECURE               = True
CSRF_COOKIE_HTTPONLY             = True
CSRF_COOKIE_SAMESITE             = 'Lax'
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', 'https://school.example.com').split(',')

# Content security
SECURE_CONTENT_TYPE_NOSNIFF      = True           # X-Content-Type-Options: nosniff
SECURE_BROWSER_XSS_FILTER        = True           # X-XSS-Protection
X_FRAME_OPTIONS                  = 'DENY'         # Clickjacking
SECURE_REFERRER_POLICY           = 'same-origin'

# ─────────────────────────────────────────────
#  CORS — lock to your frontend domain
# ─────────────────────────────────────────────

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS   = os.environ.get('CORS_ALLOWED_ORIGINS', 'https://school.example.com').split(',')
CORS_ALLOW_CREDENTIALS = True

# ─────────────────────────────────────────────
#  Email — SMTP (Gmail / AWS SES / SendGrid)
# ─────────────────────────────────────────────

EMAIL_BACKEND  = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST     = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT     = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS  = True
EMAIL_HOST_USER    = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD= os.environ.get('EMAIL_HOST_PASSWORD', '')

# ─────────────────────────────────────────────
#  Caching — Redis
# ─────────────────────────────────────────────

CACHES = {
    'default': {
        'BACKEND':  'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}

# Store sessions in cache for speed
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ─────────────────────────────────────────────
#  Throttling — stricter in production
# ─────────────────────────────────────────────

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '20/minute',
    'user': '100/minute',
}

# ─────────────────────────────────────────────
#  Logging — file + console
# ─────────────────────────────────────────────

LOG_DIR = os.environ.get('LOG_DIR', '/var/www/school_erp/logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },

    'handlers': {
        'console': {
            'class':     'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class':       'logging.handlers.RotatingFileHandler',
            'filename':    f'{LOG_DIR}/django.log',
            'maxBytes':    10 * 1024 * 1024,   # 10 MB
            'backupCount': 5,
            'formatter':   'verbose',
        },
        'error_file': {
            'class':       'logging.handlers.RotatingFileHandler',
            'filename':    f'{LOG_DIR}/errors.log',
            'maxBytes':    10 * 1024 * 1024,
            'backupCount': 5,
            'formatter':   'verbose',
            'level':       'ERROR',
        },
    },

    'root': {
        'handlers': ['console', 'file'],
        'level':    'INFO',
    },

    'loggers': {
        'django': {
            'handlers':  ['file', 'error_file'],
            'level':     'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers':  ['error_file', 'console'],
            'level':     'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers':  ['error_file'],
            'level':     'ERROR',
            'propagate': False,
        },
    },
}

# ─────────────────────────────────────────────
#  Admin URL — obscure it
# ─────────────────────────────────────────────

ADMIN_URL = os.environ.get('ADMIN_URL', 'secure-admin-2024/')