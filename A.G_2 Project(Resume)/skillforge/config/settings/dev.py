"""
Development settings for Skill Forge.
Uses SQLite for easy local development.
"""
from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ['*']

# Use SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Use console email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable whitenoise compression in dev
STORAGES = {
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

# CORS allow all in dev
CORS_ALLOW_ALL_ORIGINS = True

# JWT cookie not secure in dev
SIMPLE_JWT['AUTH_COOKIE_SECURE'] = False
