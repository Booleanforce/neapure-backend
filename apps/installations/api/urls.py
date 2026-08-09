from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.installations.api.views import InstallationRequestViewSet, ReplacementKitRequestViewSet

router = DefaultRouter()
router.register(r"requests", InstallationRequestViewSet, basename="installation-requests")
router.register(r"kits", ReplacementKitRequestViewSet, basename="replacement-kits")

urlpatterns = [
    path('', include(router.urls)),
]
