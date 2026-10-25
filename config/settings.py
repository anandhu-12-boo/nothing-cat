import os
import secrets
import sys
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent
IS_VERCEL = os.environ.get("VERCEL") == "1"
IS_RENDER = (
    os.environ.get("RENDER", "").lower() == "true"
    or bool(os.environ.get("RENDER_EXTERNAL_HOSTNAME"))
)
IS_HOSTED = IS_VERCEL or IS_RENDER

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if IS_HOSTED:
        if IS_VERCEL and sys.argv[1:2] == ["collectstatic"]:
            SECRET_KEY = secrets.token_urlsafe(50)
        else:
            raise ImproperlyConfigured(
                "Set DJANGO_SECRET_KEY in the hosting provider environment."
            )
    else:
        SECRET_KEY = "django-insecure-local-development-only"

DEBUG = os.environ.get("DJANGO_DEBUG", "").lower() in {"1", "true", "yes"}

configured_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [
    host.strip()
    for host in configured_hosts.split(",")
    if host.strip()
]
render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if render_hostname:
    ALLOWED_HOSTS.append(render_hostname)
elif IS_RENDER and not ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".onrender.com")
if IS_VERCEL:
    ALLOWED_HOSTS.append(".vercel.app")
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

csrf_trusted_origins = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in csrf_trusted_origins.split(",")
    if origin.strip()
]
if render_hostname:
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_hostname}")
if IS_VERCEL:
    CSRF_TRUSTED_ORIGINS.append("https://*.vercel.app")
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(CSRF_TRUSTED_ORIGINS))

if IS_HOSTED:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = IS_HOSTED and not DEBUG
SESSION_COOKIE_SECURE = IS_HOSTED and not DEBUG
CSRF_COOKIE_SECURE = IS_HOSTED and not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 3600 if IS_HOSTED and not DEBUG else 0

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "catalogue",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

database_url = (
    os.environ.get("DATABASE_URL")
    or os.environ.get("POSTGRES_URL_NON_POOLING")
    or os.environ.get("POSTGRES_URL")
)
if database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            database_url,
            conn_max_age=0 if IS_VERCEL else 600,
            ssl_require=IS_VERCEL,
        )
    }
elif IS_HOSTED:
    provider = "Vercel" if IS_VERCEL else "Render"
    raise ImproperlyConfigured(
        f"Configure DATABASE_URL for {provider}. "
        "SQLite is not a persistent production database."
    )
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
media_storage = {
    "BACKEND": "django.core.files.storage.FileSystemStorage",
}
if IS_RENDER and not os.environ.get("AWS_STORAGE_BUCKET_NAME"):
    if sys.argv[1:2] not in (["collectstatic"], ["migrate"]):
        raise ImproperlyConfigured(
            "Configure AWS_STORAGE_BUCKET_NAME and S3-compatible storage "
            "credentials on Render so uploaded media persists across deployments."
        )
if os.environ.get("AWS_STORAGE_BUCKET_NAME"):
    media_storage = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": os.environ["AWS_STORAGE_BUCKET_NAME"],
            "endpoint_url": os.environ.get("AWS_S3_ENDPOINT_URL"),
            "region_name": os.environ.get("AWS_S3_REGION_NAME"),
            "custom_domain": os.environ.get("AWS_S3_CUSTOM_DOMAIN"),
            "querystring_auth": False,
            "default_acl": None,
            "url_protocol": "https:",
        },
    }
STORAGES = {
    "default": media_storage,
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", str(BASE_DIR / "media")))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTHENTICATION_BACKENDS = ["catalogue.backends.EmailBackend"]
LOGIN_URL = "dashboard_login"
