"""
Django settings for the PartyVoice backend (WePlay-style social audio app).

Fill the env vars (see .env.example). This is a fresh project — nothing here
reuses any prior backend. RTC/audio is provided by ZEGOCLOUD; this server owns
identity, economy, social state, moderation, and payouts.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd party
    "rest_framework",
    "rest_framework_simplejwt",
    "channels",
    # local apps
    "accounts",
    "rtc",
    "rooms",
    "economy",
    "engagement",
    "payouts",
    "games",
    "social",
    "relationships",
    "inventory",
    "events",
    "moderation",
    "fraud",
    "observability",
    "admin_tools",
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

ROOT_URLCONF = "partyvoice.urls"
WSGI_APPLICATION = "partyvoice.wsgi.application"
ASGI_APPLICATION = "partyvoice.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

AUTH_USER_MODEL = "accounts.User"

# --- Database ---
# Defaults to SQLite for a zero-config first run; set POSTGRES_* for production.
if os.environ.get("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["POSTGRES_DB"],
            "USER": os.environ.get("POSTGRES_USER", "partyvoice"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
            "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "OPTIONS": {
                # SQLite serialises writers. With the default settings, two
                # people gifting at the same moment produce "database is
                # locked" errors — which looks like a bug in the app but isn't.
                #
                #   timeout      : wait up to 20s for the write lock instead of
                #                  failing instantly
                #   WAL          : readers don't block the writer (big win for
                #                  a chat/gift workload that reads constantly)
                #   IMMEDIATE    : take the write lock at BEGIN, so
                #                  select_for_update actually serialises rather
                #                  than deadlocking on upgrade
                #
                # This makes the promised zero-config SQLite boot survive real
                # concurrent use. For production, set POSTGRES_* — Postgres
                # handles concurrent writers natively and none of this applies.
                "timeout": 20,
                "transaction_mode": "IMMEDIATE",
                "init_command": (
                    "PRAGMA journal_mode=WAL;"
                    "PRAGMA synchronous=NORMAL;"
                    "PRAGMA busy_timeout=20000;"
                ),
            },
        }
    }

# --- Channels / Redis ---
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
if os.environ.get("REDIS_URL"):
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        }
    }
else:
    # in-memory layer so the project boots without Redis during early dev
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

# --- DRF / Auth ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "user": "120/min",
        "rtc_token": "30/min",
    },
}

# --- ZEGOCLOUD (server-side only; NEVER expose ServerSecret to the client) ---
ZEGO_APP_ID = int(os.environ.get("ZEGO_APP_ID", "0"))
ZEGO_SERVER_SECRET = os.environ.get("ZEGO_SERVER_SECRET", "")  # 32 chars
ZEGO_TOKEN_TTL_SECONDS = int(os.environ.get("ZEGO_TOKEN_TTL_SECONDS", "7200"))  # 2h

# --- Celery ---
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
