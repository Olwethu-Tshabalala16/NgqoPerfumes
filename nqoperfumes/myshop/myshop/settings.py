"""
Django settings for myshop project.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
REPOSITORY_ROOT = BASE_DIR.parents[1]
FRONTEND_DIR = REPOSITORY_ROOT / "frontend"
load_dotenv(REPOSITORY_ROOT / ".env")

# Vercel exposes these system variables to its Python runtime. Checking more
# than one keeps this true whether the generic VERCEL flag or deployment URL
# is the available signal.
ON_VERCEL = any(
    os.getenv(name)
    for name in ("VERCEL", "VERCEL_URL", "VERCEL_ENV")
)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or "dev-only-change-me"
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"


def _csv_values(value):
    """Split a comma-separated environment variable into clean values."""
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def _host_from_value(value):
    """Accept either a hostname or a URL and return its hostname only."""
    from urllib.parse import urlsplit

    value = value.strip()
    if not value:
        return ""
    parsed = urlsplit(value if "://" in value else f"//{value}")
    return (parsed.hostname or "").lower()


# A Vercel deployment can have a unique URL, a branch URL and a production
# alias. Include all runtime-provided hostnames as well as configured custom
# domains. Do not let an empty/incomplete DJANGO_ALLOWED_HOSTS setting erase
# the Vercel defaults (the usual cause of Django's DisallowedHost HTTP 400).
configured_hosts = [
    host
    for host in (
        _host_from_value(value)
        for value in _csv_values(os.getenv("DJANGO_ALLOWED_HOSTS"))
    )
    if host
]
vercel_hosts = []
if ON_VERCEL:
    vercel_hosts = [
        host
        for host in (
            _host_from_value(os.getenv(name, ""))
            for name in (
                "VERCEL_URL",
                "VERCEL_BRANCH_URL",
                "VERCEL_PROJECT_PRODUCTION_URL",
            )
        )
        if host
    ]

# This project is deployed on Vercel, so its generated and branch deployment
# URLs must be accepted even when Vercel's optional system-variable exposure
# is disabled in the dashboard.
default_hosts = ["localhost", "127.0.0.1", ".vercel.app"]

ALLOWED_HOSTS = list(
    dict.fromkeys(default_hosts + configured_hosts + vercel_hosts)
)

# CSRF trusted origins are additive too. Django requires full origins (with
# scheme), while ALLOWED_HOSTS contains hostnames only.
configured_csrf_origins = [
    origin.rstrip("/")
    for origin in _csv_values(os.getenv("CSRF_TRUSTED_ORIGINS"))
]
csrf_host_origins = []
for host in ALLOWED_HOSTS:
    if host == "*":
        continue
    origin_host = f"*{host}" if host.startswith(".") else host
    csrf_host_origins.append(f"https://{origin_host}")

csrf_host_origins.append("https://*.vercel.app")

CSRF_TRUSTED_ORIGINS = list(
    dict.fromkeys(configured_csrf_origins + csrf_host_origins)
)

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
    "axes",
    "corsheaders",
    "store",
    "storages",
]

MIDDLEWARE = [
    "store.middleware.RequireVercelConfigurationMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "axes.middleware.AxesMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "myshop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates", FRONTEND_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "store.context_processors.theme",
            ],
        },
    },
]

# Vercel resolves this module from the repository root. The root shim adds the
# nested Django project to sys.path before importing myshop.wsgi.application.
# The nested manage.py also adds the repository root for local runserver use.
WSGI_APPLICATION = "vercel_wsgi.application"

DATABASE_URL = os.getenv("DATABASE_URL")

# SQLite remains a local-development fallback only. On Vercel, the first
# middleware rejects requests until DATABASE_URL is configured, preventing
# data from being written to an ephemeral database.
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

# Protect the Django admin login against password guessing. Attempts are
# tracked in the configured database, not process memory, so the limit remains
# effective across Vercel serverless instances.
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]
AXES_FAILURE_LIMIT = 3
AXES_COOLOFF_TIME = 1  # hours
AXES_USE_ATTEMPT_EXPIRATION = True  # Each failed attempt expires after one hour.
AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_RESET_ON_SUCCESS = True
AXES_ENABLE_ACCESS_FAILURE_LOG = True

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
# The customer-facing catalogue is also a Django template. Its CSS and JS are
# collected from frontend/ and served by Vercel's static CDN at /static/.
STATICFILES_DIRS = [FRONTEND_DIR]

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
