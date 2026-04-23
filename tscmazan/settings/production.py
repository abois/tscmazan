import os

from .base import *

DEBUG = False

# ── Secrets & hosts ─────────────────────────────────────────
# SECRET_KEY DOIT venir de l'environnement. Aucun default en prod.
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

ALLOWED_HOSTS = [h for h in os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "www.tscmazan.com,tscmazan.com"
).split(",") if h]

CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get(
    "DJANGO_CSRF_TRUSTED_ORIGINS", "https://www.tscmazan.com,https://tscmazan.com"
).split(",") if o]

# ── HTTPS / headers sécu ────────────────────────────────────
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31_536_000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# ── Cookies ─────────────────────────────────────────────────
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

# ── Email (à définir via env) ───────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "Tennis Sporting Club Mazanais <noreply@tscmazan.com>"
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ── Staticfiles : manifest hashé ────────────────────────────
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

try:
    from .local import *  # noqa
except ImportError:
    pass
