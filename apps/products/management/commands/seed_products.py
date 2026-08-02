from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.products.models import Category, Product
from apps.products.constants import ProductType, ProductStatus


class Command(BaseCommand):

    help = "Seed the database with initial NeaPure product data."

    def handle(self, *args, **options):

        # -----------------------------------------------
        # Categories
        # -----------------------------------------------

        purifiers_cat, created = Category.objects.get_or_create(
            slug="water-purifiers",
            defaults={
                "name": "Water Purifiers",
                "description": "Complete water purification systems for homes and offices.",
            },
        )
        self.stdout.write(
            f"  Category: {purifiers_cat.name}"
            f" {'(created)' if created else '(exists)'}"
        )

        filters_cat, created = Category.objects.get_or_create(
            slug="filters-replacement-parts",
            defaults={
                "name": "Filters & Replacement Parts",
                "description": "Replacement filters, membranes, and components for NeaPure purifiers.",
            },
        )
        self.stdout.write(
            f"  Category: {filters_cat.name}"
            f" {'(created)' if created else '(exists)'}"
        )

        # -----------------------------------------------
        # Purifiers
        # -----------------------------------------------

        purifiers = [
            {
                "slug": "neapure-essential",
                "defaults": {
                    "name": "NeaPure Essential",
                    "sku": "NP-PUR-ESS-01",
                    "price": Decimal("18900.00"),
                    "product_type": ProductType.PURIFIER,
                    "category": purifiers_cat,
                    "warranty_duration_months": 12,
                    "is_featured": True,
                    "status": ProductStatus.ACTIVE,
                    "perfect_for": "Small families and apartments",
                    "key_features": [
                        "7-Stage Purification",
                        "RO + UV + UF Technology",
                        "8-Litre Storage Tank",
                        "Food-Grade Water Tank",
                        "Low Power Consumption",
                        "Compact Modern Design",
                        "Easy Maintenance",
                    ],
                },
            },
            {
                "slug": "neapure-pro",
                "defaults": {
                    "name": "NeaPure Pro",
                    "sku": "NP-PUR-PRO-02",
                    "price": Decimal("24900.00"),
                    "product_type": ProductType.PURIFIER,
                    "category": purifiers_cat,
                    "warranty_duration_months": 12,
                    "is_featured": True,
                    "status": ProductStatus.ACTIVE,
                    "perfect_for": "Small Families (2-4 Members)",
                    "key_features": [
                        "7-Stage RO + UV + UF Filtration",
                        "Smart LED Display",
                        "Mineral Enhancement Technology",
                        "Automatic Flush System",
                        "Filter Change Indicator",
                        "Silent Operation",
                        "Energy Efficient",
                        "Removes 99.99% Bacteria & Viruses",
                        "Low Maintenance Design",
                    ],
                },
            },
            {
                "slug": "neapure-plus",
                "defaults": {
                    "name": "NeaPure Plus",
                    "sku": "NP-PUR-PLS-03",
                    "price": Decimal("31900.00"),
                    "product_type": ProductType.PURIFIER,
                    "category": purifiers_cat,
                    "warranty_duration_months": 24,
                    "is_featured": True,
                    "status": ProductStatus.ACTIVE,
                    "perfect_for": "Medium-Sized Families (4-6 Members)",
                    "key_features": [
                        "Advanced RO + UV + Mineral Technology",
                        "Smart Filter Life Indicator",
                        "High Water Recovery System",
                        "Touch Control Panel",
                        "Fast Water Flow",
                        "Durable Food-Grade Storage Tank",
                        "Premium Finish",
                        "Smart RO Technology",
                        "UV Sterilization",
                        "Digital Display",
                        "Intelligent Filter Reminder",
                        "Large Storage Capacity",
                    ],
                },
            },
            {
                "slug": "neapure-max",
                "defaults": {
                    "name": "NeaPure Max",
                    "sku": "NP-PUR-MAX-04",
                    "price": Decimal("42900.00"),
                    "product_type": ProductType.PURIFIER,
                    "category": purifiers_cat,
                    "warranty_duration_months": 24,
                    "is_featured": True,
                    "status": ProductStatus.ACTIVE,
                    "perfect_for": "Large Families & Premium Homes",
                    "key_features": [
                        "Premium 7-Stage Smart Purification",
                        "AI-Based Smart Water Quality Monitoring",
                        "Wi-Fi Enabled Smart Control",
                        "Touch Display",
                        "Smart Filter Alert",
                        "UV + RO + UF",
                        "Mineral Booster",
                        "Premium Storage Tank",
                        "UV Sterilization Chamber",
                        "Intelligent Filter Alert System",
                        "Large Capacity Storage",
                        "Elegant Premium Design",
                    ],
                },
            },
        ]

        self.stdout.write("\n  Seeding purifiers...")

        for item in purifiers:
            product, created = Product.objects.get_or_create(
                slug=item["slug"],
                defaults=item["defaults"],
            )
            self.stdout.write(
                f"    {product.name} ({product.sku})"
                f" {'(created)' if created else '(exists)'}"
            )

        # -----------------------------------------------
        # Filters
        # -----------------------------------------------

        filters = [
            {
                "slug": "ro-membrane-filter",
                "defaults": {
                    "name": "RO Membrane Filter",
                    "sku": "NP-FLT-RO-01",
                    "price": Decimal("1290.00"),
                    "product_type": ProductType.FILTER,
                    "category": filters_cat,
                    "warranty_duration_months": 12,
                    "recommended_replacement_months": 18,
                    "is_featured": False,
                    "status": ProductStatus.ACTIVE,
                    "key_features": [
                        "Removes dissolved salts and heavy metals",
                        "Eliminates harmful bacteria and viruses",
                        "Long-lasting filtration performance",
                        "Compatible with most NeaPure RO systems",
                    ],
                },
            },
            {
                "slug": "carbon-filter",
                "defaults": {
                    "name": "Carbon Filter",
                    "sku": "NP-FLT-CARB-02",
                    "price": Decimal("690.00"),
                    "product_type": ProductType.FILTER,
                    "category": filters_cat,
                    "warranty_duration_months": 12,
                    "recommended_replacement_months": 6,
                    "is_featured": False,
                    "status": ProductStatus.ACTIVE,
                    "key_features": [
                        "Removes chlorine and unpleasant odor",
                        "Improves water taste",
                        "Protects internal filtration stages",
                        "High-quality activated carbon",
                    ],
                },
            },
            {
                "slug": "sediment-filter",
                "defaults": {
                    "name": "Sediment Filter",
                    "sku": "NP-FLT-SED-03",
                    "price": Decimal("450.00"),
                    "product_type": ProductType.FILTER,
                    "category": filters_cat,
                    "warranty_duration_months": 12,
                    "recommended_replacement_months": 5,
                    "is_featured": False,
                    "status": ProductStatus.ACTIVE,
                    "key_features": [
                        "Removes dust, rust and sand particles",
                        "Protects RO membrane",
                        "Extends purifier lifespan",
                        "Easy replacement",
                    ],
                },
            },
            {
                "slug": "mineral-cartridge",
                "defaults": {
                    "name": "Mineral Cartridge",
                    "sku": "NP-FLT-MIN-04",
                    "price": Decimal("990.00"),
                    "product_type": ProductType.FILTER,
                    "category": filters_cat,
                    "warranty_duration_months": 12,
                    "recommended_replacement_months": 12,
                    "is_featured": False,
                    "status": ProductStatus.ACTIVE,
                    "key_features": [
                        "Restores essential minerals",
                        "Improves water taste",
                        "Maintains healthy mineral balance",
                        "Premium food-grade materials",
                    ],
                },
            },
            {
                "slug": "uv-lamp",
                "defaults": {
                    "name": "UV Lamp",
                    "sku": "NP-FLT-UV-05",
                    "price": Decimal("1490.00"),
                    "product_type": ProductType.FILTER,
                    "category": filters_cat,
                    "warranty_duration_months": 12,
                    "recommended_replacement_months": 12,
                    "is_featured": False,
                    "status": ProductStatus.ACTIVE,
                    "key_features": [
                        "Kills 99.99% bacteria and viruses",
                        "Chemical-free sterilization",
                        "High-performance UV technology",
                        "Reliable long-term protection",
                    ],
                },
            },
        ]

        self.stdout.write("\n  Seeding filters...")

        for item in filters:
            product, created = Product.objects.get_or_create(
                slug=item["slug"],
                defaults=item["defaults"],
            )
            self.stdout.write(
                f"    {product.name} ({product.sku})"
                f" {'(created)' if created else '(exists)'}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "\n  Product seed data loaded successfully."
            )
        )
