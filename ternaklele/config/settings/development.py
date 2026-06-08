from .base import *

DEBUG = True

CORS_ALLOW_ALL_ORIGINS = True

# Django Debug Toolbar (opsional, install manual jika perlu)
INTERNAL_IPS = ["127.0.0.1"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
