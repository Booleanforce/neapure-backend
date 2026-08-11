import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

# Get the latest customer user
user = User.objects.filter(role='CUSTOMER').first()

if not user:
    print("No customers found. Please create one in the admin panel first.")
else:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    
    print("\n" + "="*80)
    print("CLEAN LINK FOR SCREEN RECORDING:")
    print("="*80)
    print(f"http://localhost:3000/setup-password?uid={uid}&token={token}")
    print("="*80 + "\n")