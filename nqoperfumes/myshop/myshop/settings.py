"""
Django settings for myshop project.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent.parent / ".env")

ON_VERCEL = bool(os.getenv("VERCEL"))
IS_VERCEL_BUILD = os.getenv("NQO_BUILD") == "1"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or "dev-only-change-me"
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"

# Vercel runs collectstatic during the build, before runtime-only secrets may
# be available. Enforce production secrets in api/index.py at function startup,
# not while Django is collecting static files.
if ON_VERCEL and not IS_VERCEL_BUILD and SECRET_KEY == "dev-only-change-me":
    raise ImproperlyConfigured(
        "Missing DJANGO_SECRET_KEY. Add it to the Vercel project's Environment Variables."
    )

_default_hosts = ".vercel.app,localhost,127.0.0.1" if ON_VERCEL else "localhost,127.0.0.1"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", _default_hosts).split(",")
    if host.strip()
]

_default_csrf_origins = "https://*.vercel.app" if ON_VERCEL else ""
CSRF_TRUSTED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "CSRF_TRUSTED_ORIGINS", _default_csrf_origins
    ).split(",")
    if origin.strip()
]

CORS_ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
CORS_URLS_REGEX = r"^/api/.*$"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "store",
    "storages",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "myshop.urls"

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

WSGI_APPLICATION = "myshop.wsgi.application"

DATABASE_URL = os.getenv("DATABASE_URL")

# During collectstatic, SQLite is only a harmless settings fallback; no
# database connection or migration is performed. The deployed function refuses
# to start without the real persistent PostgreSQL URL.
if ON_VERCEL and not IS_VERCEL_BUILD and not DATABASE_URL:
    raise ImproperlyConfigured(
        "Missing DATABASE_URL. Add your Supabase PostgreSQL connection string to Vercel."
    )

if DATABASE_URL:
    DATABASES = {
        "default": {
            **dj_database_url.parse(
                DATABASE_URL,
                conn_max_age=0,
                conn_health_checks=True,
                ssl_require=True,
            ),
            "CONN_MAX_AGE": 0,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Vercel terminates HTTPS at its edge proxy.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "admin@example.com")

# Email delivery and Admin 2FA remain disabled for the initial deployment.
ADMIN_2FA_ENABLE_EMAIL_OTP = False
ADMIN_2FA_EMAIL_SENDER = os.getenv(
    "ADMIN_2FA_EMAIL_SENDER",
    "admin@example.com",
)
ADMIN_2FA_EMAIL_SUBJECT = "Your login verification code"

# Supabase Storage S3-compatible configuration.
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_STORAGE_BUCKET = os.getenv(
    "SUPABASE_STORAGE_BUCKET",
    "product-images",
)
SUPABASE_STORAGE_ENDPOINT = os.getenv("SUPABASE_STORAGE_ENDPOINT")
SUPABASE_STORAGE_REGION = os.getenv("SUPABASE_STORAGE_REGION", "local")
SUPABASE_STORAGE_ACCESS_KEY_ID = os.getenv("SUPABASE_STORAGE_ACCESS_KEY_ID")
SUPABASE_STORAGE_SECRET_ACCESS_KEY = os.getenv(
    "SUPABASE_STORAGE_SECRET_ACCESS_KEY"
)

if SUPABASE_URL:
    SUPABASE_PUBLIC_STORAGE_URL = (
        f"{SUPABASE_URL}/storage/v1/object/public/"
        f"{SUPABASE_STORAGE_BUCKET}"
    )
else:
    SUPABASE_PUBLIC_STORAGE_URL = ""

AWS_STORAGE_BUCKET_NAME = SUPABASE_STORAGE_BUCKET
AWS_S3_REGION_NAME = SUPABASE_STORAGE_REGION
AWS_S3_ENDPOINT_URL = SUPABASE_STORAGE_ENDPOINT
AWS_ACCESS_KEY_ID = SUPABASE_STORAGE_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = SUPABASE_STORAGE_SECRET_ACCESS_KEY
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = False
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_ADDRESSING_STYLE = "path"
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}

STORAGES = {
    "default": {
        "BACKEND": "store.storage.SupabaseS3Storage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = (
    f"{SUPABASE_PUBLIC_STORAGE_URL}/"
    if SUPABASE_PUBLIC_STORAGE_URL
    else "/media/"
)
