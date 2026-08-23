"""
Django settings for translator_project project.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/
"""

import os
from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Read environment variables from .env file (development only).
# In production (Render), env vars are injected directly.
env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(env_file=str(BASE_DIR / ".env"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY", default="django-insecure-development-only-key-change-me")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", default="RENDER" not in os.environ)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "0.0.0.0"])  # nosec B104

RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", default="")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# CSRF trusted origins (needed for browser previews / proxies in development)
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=["http://localhost:8000", "http://127.0.0.1:8000"],
)

# URL to redirect to when login is required
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_ratelimit",
    "traductor_app",
    "user_management",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "translator_project.urls"

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
    },
]

WSGI_APPLICATION = "translator_project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

if not DEBUG:
    DATABASES = {
        "default": env.db_url("DATABASE_URL", default="postgresql://postgres:postgres@localhost/postgres"),
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Security settings (production only)
# https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/#https
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"


# Logging
# https://docs.djangoproject.com/en/4.2/topics/logging/
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "traductor_app": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
    },
}


# SciFiLingo settings
# Available fictional languages grouped by universe/franchise.
# Each group is (category_label, [(slug, language_label), ...]).
# Slugs map to funtranslations.com page slugs via LANGUAGE_SLUG_MAP in api_client.py.
SCIFILINGO_LANGUAGES = [
    (
        "Tolkien — Lord of the Rings",
        [
            ("quenya", "Quenya (High Elvish)"),
            ("sindarin", "Sindarin (Grey Elvish)"),
            ("black-speech", "Black Speech"),
        ],
    ),
    (
        "Star Wars",
        [
            ("yoda", "Yoda Speak"),
            ("sith", "Sith"),
            ("huttese", "Huttese"),
            ("mando-a", "Mando'a (Mandalorian)"),
            ("shyriiwook", "Shyriiwook (Wookiee)"),
            ("r2d2", "R2-D2"),
            ("ewokese", "Ewokese"),
            ("jawaese", "Jawaese"),
            ("gungan", "Gungan"),
            ("cheunh", "Cheunh (Chiss)"),
            ("aqualish", "Aqualish"),
        ],
    ),
    (
        "Star Trek",
        [
            ("klingon", "Klingon"),
            ("vulcan", "Vulcan"),
            ("romulan", "Romulan"),
            ("cardassian", "Cardassian (Kardasi)"),
            ("tamarian", "Tamarian"),
        ],
    ),
    (
        "Game of Thrones",
        [
            ("dothraki", "Dothraki"),
            ("valyrian", "Valyrian"),
            ("asshai", "Asshai'i"),
            ("skroth", "Skroth (White Walkers)"),
            ("lhazareen", "Lhazareen"),
        ],
    ),
    (
        "The Elder Scrolls",
        [
            ("dovahzul", "Dovahzul (Dragon Language)"),
            ("daedric", "Daedric"),
            ("aldmeris", "Aldmeris"),
            ("ayleidoon", "Ayleidoon"),
            ("tamrielic", "Tamrielic"),
        ],
    ),
    (
        "Dungeons & Dragons",
        [
            ("elvish", "Elvish"),
            ("orcish", "Orcish"),
            ("draconic", "Draconic"),
            ("halfling", "Halfling"),
            ("goblin", "Goblin"),
        ],
    ),
    (
        "World of Warcraft",
        [
            ("darnassian", "Darnassian (Night Elf)"),
            ("tel-quessir", "Tel'Quessir (Forgotten Realms)"),
        ],
    ),
    (
        "Harry Potter",
        [
            ("parseltongue", "Parseltongue"),
            ("gobbledegook", "Gobbledegook"),
            ("mermish", "Mermish"),
        ],
    ),
    (
        "Other Fictional",
        [
            ("kryptonian", "Kryptonian (DC)"),
            ("navi", "Na'vi (Avatar)"),
            ("groot", "Groot (Marvel)"),
            ("wakandan", "Wakandan (Marvel)"),
            ("hylian", "Hylian (Zelda)"),
            ("simlish", "Simlish (The Sims)"),
            ("rlyehian", "R'lyehian (Lovecraft)"),
            ("old-tongue", "Old Tongue (Wheel of Time)"),
            ("predator", "Predator / Yautja"),
            ("protoss", "Protoss / Khalani (StarCraft)"),
        ],
    ),
    (
        "Fun & Silly",
        [
            ("pirate", "Pirate Speak"),
            ("minion", "Minionese"),
            ("ferb-latin", "Ferb Latin"),
            ("valspeak", "Valspeak (Valley Girl)"),
            ("lolcat", "LOLCat"),
            ("chef", "Swedish Chef"),
        ],
    ),
]

# Optional: funtranslations API key for higher rate limits (paid plans).
# Free tier allows 60 calls/day, 5 calls/hour without a key.
FUNTRANSLATIONS_API_KEY = env("FUNTRANSLATIONS_API_KEY", default="")

# Internationalization
LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("es", "Español"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True
USE_TZ = True

# Cache: django-ratelimit requires a shared cache backend.
# In production, use Redis or memcached via env var CACHE_URL.
# LocMemCache is fine for development (single process).
CACHES = {
    "default": {
        "BACKEND": env(
            "CACHE_BACKEND",
            default="django.core.cache.backends.locmem.LocMemCache",
        ),
        "LOCATION": env("CACHE_LOCATION", default="scifilingo-dev"),
    }
}
# Silence ratelimit warning about LocMemCache in development
RATELIMIT_ENABLE = env.bool("RATELIMIT_ENABLE", default=True)

# SILENCED_SYSTEM_CHECKS: silence ratelimit E003/W001 in dev (LocMemCache)
# In production with Redis/memcached these won't appear
SILENCED_SYSTEM_CHECKS = env.list("SILENCED_SYSTEM_CHECKS", default=["django_ratelimit.E003", "django_ratelimit.W001"])
