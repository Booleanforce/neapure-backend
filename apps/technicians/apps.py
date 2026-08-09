from django.apps import AppConfig


class TechniciansConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.technicians'

    def ready(self):
        import apps.technicians.signals
