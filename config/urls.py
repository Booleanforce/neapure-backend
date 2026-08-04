from django.contrib import admin
from django.urls import path, include

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/auth/", include("apps.accounts.api.urls")),

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