from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.accounts.models import User
from shared.constants.roles import UserRole
from apps.customers.models import CustomerProfile

@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    if created and instance.role == UserRole.CUSTOMER:
        CustomerProfile.objects.get_or_create(user=instance)
