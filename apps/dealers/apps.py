from django.apps import AppConfig

class DealersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.dealers"

    def ready(self):
        import apps.dealers.signals
