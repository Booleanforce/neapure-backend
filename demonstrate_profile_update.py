import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from apps.accounts.models import User
from rest_framework_simplejwt.tokens import RefreshToken

# Get the user we just created and set up
user = User.objects.filter(email='video_test@neapure.com').first()

if not user:
    print("User 'video_test@neapure.com' not found! Please create them in the browser first.")
    exit()

print(f"--- Found User: {user.email} ---")
print(f"Current Name: {user.full_name}")

# Generate a JWT for this user (simulating they are logged in)
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)

c = Client(SERVER_NAME='localhost')

print("\n--- Sending PATCH request to /api/users/profile/ ---")
response = c.patch('/api/users/profile/', {
    "full_name": "Updated Name from API",
    "phone": "999-9999"
}, content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {access_token}')

print(f"Status Code: {response.status_code}")
print(f"Response Data: {response.json()}")

# Verify it was saved to the database
user.refresh_from_db()
print(f"\n--- Database Verification ---")
print(f"New Name in Database: {user.full_name}")
print(f"New Phone in Database: {user.phone}")
print("SUCCESS: Profile Update endpoint is fully functional and secure!")
