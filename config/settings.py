"""
Django settings for NeaPure Backend.

Technology Stack:
- Django
- Django REST Framework
- PostgreSQL
- Firebase Authentication
- Cloudinary
- WhiteNoise
- DRF Spectacular
"""

from pathlib import Path
from datetime import timedelta

from decouple import config
import cloudinary


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = config("SECRET_KEY")

DEBUG = config(
    "DEBUG",
    default=False,
    cast=bool,
)

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".vercel.app",
]


# ============================================================
# CUSTOM USER MODEL
# ============================================================

AUTH_USER_MODEL = "accounts.User"


# ============================================================
# INSTALLED APPS
# ============================================================

INSTALLED_APPS = [
    # --------------------------------------------------------
    # Django
    # --------------------------------------------------------

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # --------------------------------------------------------
    # Third Party
    # --------------------------------------------------------

    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "cloudinary",
    "cloudinary_storage",
    "rest_framework_simplejwt",
    "django_filters",

    # --------------------------------------------------------
    # Local Apps
    # --------------------------------------------------------

    "apps.accounts",
    "apps.customers",
    "apps.dealers",
    "apps.products",
    "apps.product_registrations",
    "apps.installations",
    "apps.technicians",
    "apps.notifications",
    "apps.ai_assistant",
    "apps.service_bookings",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.security.SecurityMiddleware",

    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URL CONFIGURATION
# ============================================================

ROOT_URLCONF = "config.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        "DIRS": [],

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


# ============================================================
# WSGI
# ============================================================

WSGI_APPLICATION = "config.wsgi.application"


# ============================================================
# DATABASE
# ============================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",

        "NAME": config("DB_NAME"),

        "USER": config("DB_USER"),

        "PASSWORD": config("DB_PASSWORD"),

        "HOST": config("DB_HOST"),

        "PORT": config("DB_PORT"),

        "OPTIONS": {
            "sslmode": "require",
        },
    }
}


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation.MinimumLengthValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation.CommonPasswordValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Dhaka"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"


# ============================================================
# CLOUDINARY
# ============================================================


CLOUDINARY_STORAGE = {
    "CLOUD_NAME": config("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": config("CLOUDINARY_API_KEY"),
    "API_SECRET": config("CLOUDINARY_API_SECRET"),
    "SECURE": True,

    # Existing Cloudinary assets are under media/
    "PREFIX": "media",
}

cloudinary.config(
    cloud_name=config("CLOUDINARY_CLOUD_NAME"),
    api_key=config("CLOUDINARY_API_KEY"),
    api_secret=config("CLOUDINARY_API_SECRET"),
    secure=True,
)

DEFAULT_FILE_STORAGE = (
    "cloudinary_storage.storage.MediaCloudinaryStorage"
)

# ============================================================
# FILE STORAGE
# ============================================================

STORAGES = {
    "default": {
        "BACKEND":
            "cloudinary_storage.storage.MediaCloudinaryStorage",
    },

    "staticfiles": {
        "BACKEND":
            "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# ============================================================
# MEDIA
# ============================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# CORS
# ============================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",

    "https://nea-pure.vercel.app",
]

CORS_ALLOW_CREDENTIALS = True


# ============================================================
# DJANGO REST FRAMEWORK
# ============================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",

        "apps.accounts.authentication.FirebaseAuthentication",
    ),

    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),

    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",

        "rest_framework.filters.SearchFilter",

        "rest_framework.filters.OrderingFilter",
    ),

    "DEFAULT_PAGINATION_CLASS":
        "shared.pagination.pagination.CustomPagination",

    "PAGE_SIZE": 10,

    "DEFAULT_SCHEMA_CLASS":
        "drf_spectacular.openapi.AutoSchema",
}


# ============================================================
# SWAGGER / DRF SPECTACULAR
# ============================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "NeaPure API",

    "DESCRIPTION":
        "NeaPure Smart Water Care Platform API",

    "VERSION": "1.0.0",
}


# ============================================================
# FIREBASE
# ============================================================

FIREBASE_CREDENTIALS = config(
    "FIREBASE_CREDENTIALS"
)


# ============================================================
# EMAIL
# ============================================================

EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
)

EMAIL_HOST = config("EMAIL_HOST")

EMAIL_PORT = config(
    "EMAIL_PORT",
    cast=int,
)

EMAIL_USE_TLS = config(
    "EMAIL_USE_TLS",
    cast=bool,
)

EMAIL_HOST_USER = config(
    "EMAIL_HOST_USER"
)

EMAIL_HOST_PASSWORD = config(
    "EMAIL_HOST_PASSWORD"
)

DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL"
)


# ============================================================
# FRONTEND
# ============================================================

FRONTEND_URL = config(
    "FRONTEND_URL"
)


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)


# ============================================================
# JWT
# ============================================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":
        timedelta(hours=8),

    "REFRESH_TOKEN_LIFETIME":
        timedelta(days=30),

    "ROTATE_REFRESH_TOKENS":
        True,
}


# ============================================================
# CSRF
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    "https://nea-pure.vercel.app",

    "https://neapure-backend-eta.vercel.app",
]