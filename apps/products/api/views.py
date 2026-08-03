from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from shared.constants.roles import UserRole
from apps.products.models import Product, RegisteredProduct
from apps.products.api.serializers import ProductSerializer, RegisteredProductSerializer

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public catalog of products. Dealers and customers can view them.
    """
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "sku"]
    ordering_fields = ["name"]
    ordering = ["name"]

class RegisteredProductViewSet(viewsets.ModelViewSet):
    """
    API for registering and viewing owned products.
    """
    serializer_class = RegisteredProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["serial_number", "customer__email", "product__name"]
    ordering_fields = ["purchase_date", "created_at"]
    ordering = ["-purchase_date"]
    filterset_fields = ["product"]

    def get_queryset(self):
        user = self.request.user
        queryset = RegisteredProduct.objects.select_related("product", "customer", "dealer")
        
        if user.role == UserRole.CUSTOMER:
            return queryset.filter(customer=user)
        elif user.role == UserRole.DEALER:
            return queryset.filter(dealer=user)
        
        # Admin gets everything
        return queryset

    def create(self, request, *args, **kwargs):
        # Only Dealers or Admins can register a product
        if request.user.role == UserRole.CUSTOMER:
            return Response({"error": "Customers cannot register products directly."}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        dealer = request.user if request.user.role == UserRole.DEALER else None
        
        serializer.save(dealer=dealer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
