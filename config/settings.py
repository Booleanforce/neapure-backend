"""
Django settings for NeaPure Backend.

Technology Stack
----------------
- Django
- Django REST Framework
- PostgreSQL
- Firebase Authentication
- Cloudinary
- WhiteNoise
- DRF Spectacular

Author: NeaPure Development Team
"""

from pathlib import Path
from decouple import config
import cloudinary
from datetime import timedelta

# -------------------------------------------------
# Base Directory
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------
# Security
# -------------------------------------------------

SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = [
    ".vercel.app",
    "localhost",
    "127.0.0.1",
]

# -------------------------------------------------
# Custom User Model
# -------------------------------------------------

AUTH_USER_MODEL = "accounts.User"

# -------------------------------------------------
# Installed Apps
# -------------------------------------------------

INSTALLED_APPS = [

    # Django Apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third Party
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "cloudinary",
    "cloudinary_storage",
    "rest_framework_simplejwt",
    "django_filters",

    # Local Apps
    "apps.accounts",
    "apps.customers",
    "apps.dealers",
    "apps.installations",
    "apps.products",
    "apps.product_registrations",
    "apps.ai_assistant",
    "apps.service_bookings",

]

# -------------------------------------------------
# Middleware
# -------------------------------------------------

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

# -------------------------------------------------
# URL Configuration
# -------------------------------------------------

ROOT_URLCONF = "config.urls"

# -------------------------------------------------
# Templates
# -------------------------------------------------

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

# -------------------------------------------------
# WSGI
# -------------------------------------------------

WSGI_APPLICATION = "config.wsgi.application"

# -------------------------------------------------
# Database
# -------------------------------------------------

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

# -------------------------------------------------
# Password Validation
# -------------------------------------------------

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

# -------------------------------------------------
# Internationalization
# -------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Dhaka"

USE_I18N = True

USE_TZ = True

# -------------------------------------------------
# Static Files
# -------------------------------------------------

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"


# -------------------------------------------------
# Media Files
# -------------------------------------------------

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"

# -------------------------------------------------
# Cloudinary
# -------------------------------------------------

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": config("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": config("CLOUDINARY_API_KEY"),
    "API_SECRET": config("CLOUDINARY_API_SECRET"),
    "SECURE": True,
}

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# -------------------------------------------------
# CORS
# -------------------------------------------------

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://nea-pure.vercel.app",
]

CORS_ALLOW_CREDENTIALS = True

# -------------------------------------------------
# Django REST Framework
# -------------------------------------------------

REST_FRAMEWORK = {

    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # "apps.accounts.authentication.FirebaseAuthentication",
    ),

    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),

    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",

    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),

    "DEFAULT_PAGINATION_CLASS":
        "shared.pagination.pagination.CustomPagination",

    "PAGE_SIZE": 10,
    "EXCEPTION_HANDLER":
        "shared.exceptions.custom_exception_handler",

    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# -------------------------------------------------
# Swagger
# -------------------------------------------------

SPECTACULAR_SETTINGS = {

    "TITLE": "NeaPure API",

    "DESCRIPTION": "NeaPure Smart Water Care Platform API",

    "VERSION": "1.0.0",

    "ENUM_NAME_OVERRIDES": {
        "ProductStatusEnum": "apps.products.constants.ProductStatus",
        "InstallationStatusEnum": "apps.product_registrations.constants.InstallationStatus",
        "WarrantyStatusEnum": "apps.product_registrations.constants.WarrantyStatus",
    },

}

# -------------------------------------------------
# Firebase
# -------------------------------------------------

FIREBASE_CREDENTIALS = config("FIREBASE_CREDENTIALS")

# -------------------------------------------------
# Email
# -------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = config("EMAIL_HOST")

EMAIL_PORT = config("EMAIL_PORT", cast=int)

EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool)

EMAIL_HOST_USER = config("EMAIL_HOST_USER")

EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")

# -------------------------------------------------
# Frontend
# -------------------------------------------------

FRONTEND_URL = config("FRONTEND_URL")

# -------------------------------------------------
# Default Primary Key
# -------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# -------------------------------------------------
# JWT Settings
# -------------------------------------------------

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
}
CORS_ALLOW_ALL_ORIGINS = True

CSRF_TRUSTED_ORIGINS = [
    "https://nea-pure.vercel.app",
    "https://neapure-backend-eta.vercel.app",
]