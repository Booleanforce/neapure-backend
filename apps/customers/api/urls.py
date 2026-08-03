from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.customers.api.views import CustomerViewSet

router = DefaultRouter()
router.register(r'', CustomerViewSet, basename='customer')

urlpatterns = [
    path('', include(router.urls)),
]
