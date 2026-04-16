from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-zcm=g4*$8%a)g(z8n&5h*je!(o=3k!xp_7)hxe=*h&efdd%qn8"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CSRF_TRUSTED_ORIGINS = [
    "https://*.ngrok-free.app",
    "https://*.ngrok.io",
    "https://delta-guerdonless-unputridly.ngrok-free.dev",
]


try:
    from .local import *
except ImportError:
    pass
