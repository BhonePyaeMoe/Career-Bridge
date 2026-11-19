"""Production settings for the single-service CareerBridge deployment."""
import os
from pathlib import Path

import dj_database_url

from .settings import *

DEBUG = False
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith("django-insecure-"):
    raise ValueError("Set DJANGO_SECRET_KEY to a randomly generated production secret.")

public_host = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
extra_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "")
ALLOWED_HOSTS = list(dict.fromkeys(
    host.strip() for host in [public_host, *extra_hosts.split(","), "healthcheck.railway.app"]
    if host.strip()
))
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

DATABASES = {"default": dj_database_url.parse(os.environ["DATABASE_URL"])}
if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
    raise ValueError("DATABASE_URL must point to PostgreSQL.")

MEDIA_ROOT = Path(os.environ["RAILWAY_VOLUME_MOUNT_PATH"])
STATIC_URL = "/static/"
ANGULAR_ROOT = BASE_DIR / "angular_dist"
WHITENOISE_ROOT = ANGULAR_ROOT
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
ROOT_URLCONF = "config.railway_urls"

# Railway terminates HTTPS at its public edge.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r"^healthz/$"]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
