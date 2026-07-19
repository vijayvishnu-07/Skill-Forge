import os
from django.core.wsgi import get_wsgi_application

# Production entrypoint (used by gunicorn). Local dev still uses manage.py,
# which defaults to config.settings.dev. Override with the DJANGO_SETTINGS_MODULE
# env var if you need something different on your host.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
application = get_wsgi_application()
