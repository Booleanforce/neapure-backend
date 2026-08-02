import django_filters

from .models import Product


class ProductFilter(django_filters.FilterSet):

    category = django_filters.CharFilter(
        field_name="category__slug",
        lookup_expr="exact",
        label="Category slug",
    )

    category_id = django_filters.UUIDFilter(
        field_name="category__id",
        lookup_expr="exact",
        label="Category UUID",
    )

    product_type = django_filters.CharFilter(
        field_name="product_type",
        lookup_expr="exact",
    )

    status = django_filters.CharFilter(
        field_name="status",
        lookup_expr="exact",
    )

    is_featured = django_filters.BooleanFilter(
        field_name="is_featured",
    )

    min_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="gte",
        label="Minimum price",
    )

    max_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="lte",
        label="Maximum price",
    )

    class Meta:

        model = Product

        fields = [
            "category",
            "category_id",
            "product_type",
            "status",
            "is_featured",
            "min_price",
            "max_price",
        ]
