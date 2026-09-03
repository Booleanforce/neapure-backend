import os
import django
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from apps.accounts.models import User
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator

c = Client(SERVER_NAME='localhost')
user = User.objects.filter(email='new_dealer@neapure.com').first()

# 1. Test Password Setup
token = PasswordResetTokenGenerator().make_token(user)
uid = urlsafe_base64_encode(force_bytes(user.pk))

print("--- Testing Password Setup ---")
response = c.post('/api/auth/setup-password/', {
    "uid": uid,
    "token": token,
    "password": "NewSecurePassword123!"
}, content_type='application/json')
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")

access_token = response.json().get('access')

# 2. Test Profile PATCH
print("\n--- Testing Profile Update ---")
response = c.patch('/api/users/profile/', {
    "full_name": "Updated Dealer Name"
}, content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {access_token}')

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
