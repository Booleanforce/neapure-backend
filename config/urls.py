from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/auth/", include("apps.accounts.api.urls")),

    # Users / Accounts
    path("api/", include("apps.accounts.urls")),

    # Customers
    path("api/customers/", include("apps.customers.api.urls")),

    # Dealers
    path("api/dealers/", include("apps.dealers.api.urls")),

    # Products
    path("api/products/", include("apps.products.api.urls")),

    # Installations
    path("api/installations/", include("apps.installations.api.urls")),
    # Products
    path("api/products/", include("apps.products.urls")),

    # Registrations
    path("api/registrations/", include("apps.product_registrations.urls")),

    # AI Assistant
    path("api/ai/", include("apps.ai_assistant.urls")),

    # Service Bookings
    path("api/", include("apps.service_bookings.urls")),

    # Technicians
    path("api/technicians/", include("apps.technicians.api.urls")),

    # Notifications
    path("api/notifications/", include("apps.notifications.api.urls")),

    # Technicians
    path("api/technicians/", include("apps.technicians.api.urls")),

    # Notifications
    path("api/notifications/", include("apps.notifications.api.urls")),

    # Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]


# ============================================================
# MEDIA FILES - DEVELOPMENT ONLY
# ============================================================

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )