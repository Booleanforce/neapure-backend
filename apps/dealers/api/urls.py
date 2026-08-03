from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.dealers.api.views import AdminDealerViewSet, DealerMeView

router = DefaultRouter()
router.register(r'admin/dealers', AdminDealerViewSet, basename='admin-dealer')

urlpatterns = [
    path('me/', DealerMeView.as_view(), name='dealer-me'),
    path('', include(router.urls)),
]
