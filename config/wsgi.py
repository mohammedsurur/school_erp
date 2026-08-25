# config/wsgi.py

import os
from dotenv import load_dotenv
from django.core.wsgi import get_wsgi_application

# Load .env before Django initialises
# load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Load .env for local development
# On Railway, env vars are set in the dashboard — dotenv is ignored
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Railway sets RAILWAY_ENVIRONMENT automatically
# so settings/__init__.py will pick railway.py
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'config.settings'
)

application = get_wsgi_application()