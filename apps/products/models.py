from django.db import models
from shared.mixins.base import BaseModel
from shared.mixins.soft_delete import SoftDeleteModel
from apps.accounts.models import User

class Product(SoftDeleteModel, BaseModel):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "products"
        ordering = ["name"]

    def __str__(self):
        return self.name

class RegisteredProduct(SoftDeleteModel, BaseModel):
    product = models.ForeignKey(Product, on_delete=models.RESTRICT, related_name="registrations")
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_products")
    dealer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="sold_products")
    serial_number = models.CharField(max_length=100, unique=True)
    purchase_date = models.DateField()
    warranty_end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "registered_products"
        ordering = ["-purchase_date"]

    def __str__(self):
        return f"{self.product.name} - {self.serial_number}"
