import os
import django
import uuid
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import requests
from apps.products.models import RegisteredProduct

User = get_user_model()
BASE_URL = "http://127.0.0.1:8000"

def run_test_flow():
    print("--- Starting End-to-End Installation Flow Test ---\n")
    
    # 1. Gather Demo Users
    dealer = User.objects.filter(role="DEALER").first()
    super_admin = User.objects.filter(role="SUPER_ADMIN").first()
    ops_admin = User.objects.filter(role="OPERATIONS_ADMIN").first()
    technician = User.objects.filter(role="TECHNICIAN").first()
    customer = User.objects.filter(role="CUSTOMER").first()
    
    if not all([dealer, super_admin, ops_admin, technician, customer]):
        print("Missing required demo users. Please generate demo data first.")
        return
    
    reg_product = RegisteredProduct.objects.filter(customer=customer).first()
    
    def get_headers(user):
        refresh = RefreshToken.for_user(user)
        return {'Authorization': f'Bearer {str(refresh.access_token)}'}
    
    # STEP 1: Dealer creates a request
    print("1. DEALER: Requesting new installation...")
    res = requests.post(f'{BASE_URL}/api/installations/requests/', json={
        "customer": str(customer.id),
        "registered_product": str(reg_product.id)
    }, headers=get_headers(dealer))
    if res.status_code != 201:
        print(f"FAILED (Create Request): {res.status_code} - {res.text}")
        return
    request_id = res.json()['id']
    print(f"   SUCCESS! Created InstallationRequest ID: {request_id}")
    print(f"   Status: {res.json()['status']}\n")
    
    # STEP 2: Super Admin approves request
    print("2. SUPER ADMIN: Approving request...")
    res = requests.patch(f'{BASE_URL}/api/installations/requests/{request_id}/approve/', json={
        "notes": "Approved by automated test."
    }, headers=get_headers(super_admin))
    if res.status_code != 200:
        print(f"FAILED (Approve): {res.status_code} - {res.text}")
        return
    print(f"   SUCCESS! Request Approved.")
    print(f"   Status: {res.json()['status']}\n")
    
    # STEP 3: Ops Admin assigns technician
    print("3. OPS ADMIN: Assigning technician...")
    res = requests.post(f'{BASE_URL}/api/installations/requests/{request_id}/assign_technician/', json={
        "technician_id": str(technician.id),
        "scheduled_date": (timezone.now() + timedelta(days=1)).isoformat(),
        "address": "123 Test E2E Street"
    }, headers=get_headers(ops_admin))
    if res.status_code != 200:
        print(f"FAILED (Assign): {res.status_code} - {res.text}")
        return
    print(f"   SUCCESS! Technician Assigned.")
    print(f"   Status: {res.json()['status']}\n")
    
    # STEP 4: Technician accepts job
    print("4. TECHNICIAN: Accepting job...")
    res = requests.post(f'{BASE_URL}/api/installations/requests/{request_id}/accept_job/', headers=get_headers(technician))
    if res.status_code != 200:
        print(f"FAILED (Accept): {res.status_code} - {res.text}")
        return
    print(f"   SUCCESS! Job Accepted.")
    print(f"   Status: {res.json()['status']}\n")
    
    # STEP 5: Technician checks in
    print("5. TECHNICIAN: Checking in at site...")
    res = requests.post(f'{BASE_URL}/api/installations/requests/{request_id}/check_in/', json={
        "location": "GPS: 12.34, 56.78"
    }, headers=get_headers(technician))
    if res.status_code != 200:
        print(f"FAILED (Check-In): {res.status_code} - {res.text}")
        return
    print(f"   SUCCESS! Checked In.")
    print(f"   Status: {res.json()['status']}\n")
    
    # STEP 6: Technician uploads photos
    print("6. TECHNICIAN: Uploading Before & After photos...")
    
    # Create dummy images
    from io import BytesIO
    from django.core.files.uploadedfile import SimpleUploadedFile
    img = BytesIO(b"dummy image data")
    
    # Before Photo
    res1 = requests.post(f'{BASE_URL}/api/installations/requests/{request_id}/upload_photos/', data={
        "photo_type": "BEFORE"
    }, files={
        "photo": ("before.jpg", img.read(), "image/jpeg")
    }, headers=get_headers(technician))
    
    img.seek(0)
    # After Photo
    res2 = requests.post(f'{BASE_URL}/api/installations/requests/{request_id}/upload_photos/', data={
        "photo_type": "AFTER"
    }, files={
        "photo": ("after.jpg", img.read(), "image/jpeg")
    }, headers=get_headers(technician))
    
    if res1.status_code != 201 or res2.status_code != 201:
        print(f"FAILED (Upload Photos): Before={res1.status_code} {res1.text}, After={res2.status_code} {res2.text}")
        return
    print(f"   SUCCESS! Photos Uploaded.\n")
    
    # STEP 7: Technician submits checklist
    print("7. TECHNICIAN: Submitting checklist...")
    res = requests.post(f'{BASE_URL}/api/installations/requests/{request_id}/checklist/', json={
        "data": {
            "site_inspected": True,
            "plumbing_ready": True,
            "unit_installed": True,
            "water_tested": True,
            "leaks_checked": True,
            "customer_briefed": True
        }
    }, headers=get_headers(technician))
    if res.status_code != 201:
        print(f"FAILED (Checklist): {res.status_code} - {res.text}")
        return
    print(f"   SUCCESS! Checklist Submitted.\n")
    
    # STEP 8: Technician submits signature
    print("8. TECHNICIAN: Uploading Customer Signature...")
    img.seek(0)
    res = requests.post(f'{BASE_URL}/api/installations/requests/{request_id}/signature/', files={
        "signature_image": ("signature.jpg", img.read(), "image/jpeg")
    }, headers=get_headers(technician))
    if res.status_code != 201:
        print(f"FAILED (Signature): {res.status_code} - {res.text}")
        return
    print(f"   SUCCESS! Signature Uploaded.\n")
    
    # STEP 9: Technician completes job
    print("9. TECHNICIAN: Completing Job...")
    res = requests.post(f'{BASE_URL}/api/installations/requests/{request_id}/complete/', headers=get_headers(technician))
    if res.status_code != 200:
        print(f"FAILED (Complete Job): {res.status_code} - {res.text}")
        return
    print(f"   SUCCESS! Job Completed.")
    print(f"   Final Status: {res.json()['status']}\n")
    
    print("🎉 ALL TESTS PASSED! The end-to-end flow is fully operational!")

if __name__ == "__main__":
    run_test_flow()
