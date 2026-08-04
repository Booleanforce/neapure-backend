from rest_framework.routers import DefaultRouter

from .views import ProductRegistrationViewSet

router = DefaultRouter()

router.register(
    "registrations",
    ProductRegistrationViewSet,
    basename="registration",
)

urlpatterns = router.urls
