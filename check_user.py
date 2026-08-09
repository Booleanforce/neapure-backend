import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.filter(email='admin@neapure.com').first()
if not user:
    user = User.objects.first()

if user:
    print(f"Token was generated for: {user.email} (ID: {user.id})")
else:
    print("No user found")
