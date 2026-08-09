from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.accounts.models import User
from shared.constants.roles import UserRole
from apps.technicians.models import TechnicianProfile

@receiver(post_save, sender=User)
def create_technician_profile(sender, instance, created, **kwargs):
    if created and instance.role == UserRole.TECHNICIAN:
        TechnicianProfile.objects.get_or_create(user=instance)
