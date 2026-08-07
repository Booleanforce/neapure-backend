import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
user = User.objects.filter(email='admin@neapure.com').first()
if not user:
    user = User.objects.first()

if user:
    refresh = RefreshToken.for_user(user)
    print(str(refresh.access_token))
else:
    print("NO_USER")
