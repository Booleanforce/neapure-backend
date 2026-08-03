from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.installations.api.views import InstallationRequestViewSet

router = DefaultRouter()
router.register(r'requests', InstallationRequestViewSet, basename='installation-request')

urlpatterns = [
    path('', include(router.urls)),
]
