import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.services.account_service import AccountService
from django.core import mail
from django.contrib.auth import get_user_model

User = get_user_model()
from django.conf import settings
settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Delete test user if exists
User.objects.filter(email='new_dealer@neapure.com').delete()

print(f"Outbox before: {len(mail.outbox) if hasattr(mail, 'outbox') else 0}")

import uuid

user = AccountService.create_user({
    "email": "new_dealer@neapure.com",
    "password": "TemporaryPassword123!",
    "full_name": "New Dealer Test",
    "phone": "555-1234",
    "role": "DEALER",
    "firebase_uid": str(uuid.uuid4())
})

print(f"Outbox after: {len(mail.outbox)}")
if len(mail.outbox) > 0:
    email = mail.outbox[0]
    print(f"Email subject: {email.subject}")
    print(f"Email to: {email.to}")
    print(f"Email body: {email.body[:100]}...")
