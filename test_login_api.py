import requests
import json
import random
import string

BASE_URL = "http://127.0.0.1:8000/api/auth"

def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def test_auth():
    print("Testing Registration...")
    email = f"test_login_{random_string()}@example.com"
    password = "SecurePassword123!"
    
    reg_data = {
        "email": email,
        "password": password,
        "first_name": "Test",
        "last_name": "Login",
        "phone_number": "+1234567890",
        "role": "DEALER"
    }
    
    r = requests.post(f"{BASE_URL}/register/", json=reg_data)
    if r.status_code == 201:
        print("Registration successful!")
    else:
        print("Registration failed:", r.status_code, r.text)
        return
        
    print("\nTesting Login...")
    login_data = {
        "email": email,
        "password": password
    }
    
    r2 = requests.post(f"{BASE_URL}/login/", json=login_data)
    if r2.status_code == 200:
        print("Login successful!")
        print("Access Token length:", len(r2.json().get('access', '')))
    else:
        print("Login failed:", r2.status_code, r2.text)

if __name__ == "__main__":
    test_auth()
