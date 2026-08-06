from rest_framework.routers import DefaultRouter
from apps.service_bookings.api.views import ServiceBookingViewSet

app_name = "service_bookings"

router = DefaultRouter()
router.register(r'service-bookings', ServiceBookingViewSet, basename='service-booking')

urlpatterns = router.urls
