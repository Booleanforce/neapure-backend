<<<<<<< HEAD
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.products.api.views import ProductViewSet, RegisteredProductViewSet

router = DefaultRouter()
router.register(r'catalog', ProductViewSet, basename='product-catalog')
router.register(r'registered', RegisteredProductViewSet, basename='registered-product')

urlpatterns = [
    path('', include(router.urls)),
]
=======
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, ProductViewSet

router = DefaultRouter()

router.register(
    "categories",
    CategoryViewSet,
    basename="category",
)

router.register(
    "products",
    ProductViewSet,
    basename="product",
)

urlpatterns = router.urls
>>>>>>> origin/syed
