from pathlib import Path
import os
from urllib.parse import urlsplit
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

IS_VERCEL = os.environ.get("VERCEL") == "1" or any(
    os.environ.get(name) for name in ("VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL")
)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY and IS_VERCEL:
    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY in the Vercel project environment.")
SECRET_KEY = SECRET_KEY or "django-insecure-local-development-key-change-before-deployment"

DEBUG = os.environ.get("DJANGO_DEBUG", "0" if IS_VERCEL else "1") == "1"

def _host_name(value):
    value = value.strip()
    if not value:
        return ""
    if "://" in value:
        value = urlsplit(value).netloc
    value = value.split("/", 1)[0]
    if value.startswith("["):
        return value.split("]", 1)[0] + "]"
    return value.rsplit(":", 1)[0].lower()

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
for env_name in ("DJANGO_ALLOWED_HOSTS", "VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL"):
    for configured_host in os.environ.get(env_name, "").split(","):
        host = _host_name(configured_host)
        if host and host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)

CSRF_TRUSTED_ORIGINS = [
    origin.strip().rstrip("/") 
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") 
    if origin.strip()
]

for env_name in ("VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL"):
    for configured_host in os.environ.get(env_name, "").split(","):
        host = _host_name(configured_host)
        origin = f"https://{host}" if host else ""
        if origin and origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

if IS_VERCEL or any(os.environ.get(name) for name in ("VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL")):
    # Vercel terminates TLS and forwards the original scheme in this header.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "logbook.apps.LogbookConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "attachment_desk.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "attachment_desk.wsgi.application"
ASGI_APPLICATION = "attachment_desk.asgi.application"

DATABASE_URL = os.environ.get("DATABASE_URL")
if IS_VERCEL and not DATABASE_URL:
    raise ImproperlyConfigured(
        "Attach a PostgreSQL database to this Vercel project and set DATABASE_URL. "
        "SQLite is only suitable for local development."
    )

if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=60,
            ssl_require=IS_VERCEL,
        )
    }
    if DATABASES["default"]["ENGINE"].endswith("postgresql"):
        DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
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
TIME_ZONE = "Africa/Harare"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"
