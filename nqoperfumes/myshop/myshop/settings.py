"""
Django settings for myshop project.
"""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "localhost,127.0.0.1",
    ).split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "store",
    "storages",
    "django_admin_2fa_plus",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

ROOT_URLCONF = "myshop.urls"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

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

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0,
            conn_health_checks=True,
            ssl_require=True,
        )
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

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

ADMIN_2FA_ENABLE_EMAIL_OTP = True
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
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

MEDIA_URL = (
    f"{SUPABASE_PUBLIC_STORAGE_URL}/"
    if SUPABASE_PUBLIC_STORAGE_URL
    else "/media/"
)
