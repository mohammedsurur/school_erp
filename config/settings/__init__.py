# config/settings/__init__.py
# Auto-selects the right settings file based on environment.

import os

# Railway automatically sets RAILWAY_ENVIRONMENT
if os.environ.get('RAILWAY_ENVIRONMENT'):
    from .railway import *

elif os.environ.get('DJANGO_ENV', '').lower() == 'production':
    from .production import *

else:
    from .development import *