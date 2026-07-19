"""
Production settings for Skill Forge.
Uses PostgreSQL and stricter security.
"""
from .base import *  # noqa: F401, F403

DEBUG = False

# Database - PostgreSQL
DATABASES = {
    'default': env.db('DATABASE_URL', default='postgres://postgres:password@localhost:5432/skillforge')
}

# Trust your deployed domain(s) for CSRF (required for HTTPS POST/login/admin to work).
# Set this env var on your host, e.g. CSRF_TRUSTED_ORIGINS=https://your-app.onrender.com
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# JWT secure cookie
SIMPLE_JWT['AUTH_COOKIE_SECURE'] = True

# Production email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# CORS restricted
CORS_ALLOW_ALL_ORIGINS = False
