import os
import django
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid

# Ensure Django is set up if running outside shell, though we'll run it in shell
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

User = get_user_model()
from shared.constants.roles import UserRole
from apps.products.models import RegisteredProduct
from apps.installations.models import InstallationRequest, InstallationStatus
from apps.technicians.models import TechnicianJob, JobStatus, JobType

def generate_demo_data():
    print("Generating demo data...")
    
    # 1. Create/Get Operations Admin
    ops_admin, _ = User.objects.get_or_create(
        email="ops.admin@neapure.com",
        defaults={"role": UserRole.OPERATIONS_ADMIN, "is_active": True, "firebase_uid": str(uuid.uuid4())[:28]}
    )
    if not ops_admin.password:
        ops_admin.set_password("Password123!")
        ops_admin.save()
        
    # 2. Create/Get Technician
    tech1, _ = User.objects.get_or_create(
        email="tech1@neapure.com",
        defaults={"role": UserRole.TECHNICIAN, "is_active": True, "firebase_uid": str(uuid.uuid4())[:28]}
    )
    if not tech1.password:
        tech1.set_password("Password123!")
        tech1.save()
        
    tech2, _ = User.objects.get_or_create(
        email="tech2@neapure.com",
        defaults={"role": UserRole.TECHNICIAN, "is_active": True, "firebase_uid": str(uuid.uuid4())[:28]}
    )
    if not tech2.password:
        tech2.set_password("Password123!")
        tech2.save()

    # 3. Get a Dealer
    dealer = User.objects.filter(role=UserRole.DEALER).first()
    if not dealer:
        dealer, _ = User.objects.get_or_create(
            email="demo.dealer@neapure.com",
            defaults={"role": UserRole.DEALER, "is_active": True, "firebase_uid": str(uuid.uuid4())[:28]}
        )
        dealer.set_password("Password123!")
        dealer.save()

    # 4. Get a Customer
    customer = User.objects.filter(role=UserRole.CUSTOMER).first()
    if not customer:
        customer, _ = User.objects.get_or_create(
            email="demo.customer@neapure.com",
            defaults={"role": UserRole.CUSTOMER, "is_active": True, "firebase_uid": str(uuid.uuid4())[:28]}
        )
        customer.set_password("Password123!")
        customer.save()
        
    # 5. Get/Create RegisteredProduct for the customer
    registered_product = RegisteredProduct.objects.filter(customer=customer).first()
    if not registered_product:
        # Assuming Product model exists, let's just fetch one or create a dummy product
        from apps.products.models import Product
        product = Product.objects.first()
        if not product:
            product = Product.objects.create(name="NeaPure Water Filter", sku="NP-WF-001", price=199.99)
        registered_product = RegisteredProduct.objects.create(
            customer=customer,
            product=product,
            serial_number="SN-123456789",
            dealer=dealer,
            purchase_date=timezone.now().date()
        )
        
    # 6. Create 8 Installation Requests
    # Wipe old ones for a clean slate
    InstallationRequest.objects.all().delete()
    TechnicianJob.objects.all().delete()
    
    # Request 1 & 2: PENDING_APPROVAL
    print("Creating PENDING_APPROVAL requests...")
    for i in range(2):
        InstallationRequest.objects.create(
            customer=customer,
            dealer=dealer,
            registered_product=registered_product,
            status=InstallationStatus.PENDING_APPROVAL
        )
        
    # Request 3 & 4: APPROVED
    print("Creating APPROVED requests...")
    for i in range(2):
        InstallationRequest.objects.create(
            customer=customer,
            dealer=dealer,
            registered_product=registered_product,
            status=InstallationStatus.APPROVED
        )

    # Request 5 & 6: ASSIGNED (Requires TechnicianJob)
    print("Creating ASSIGNED requests...")
    for i in range(2):
        req = InstallationRequest.objects.create(
            customer=customer,
            dealer=dealer,
            registered_product=registered_product,
            status=InstallationStatus.ASSIGNED
        )
        TechnicianJob.objects.create(
            technician=tech1 if i == 0 else tech2,
            installation_request=req,
            job_type=JobType.INSTALLATION,
            customer=customer,
            dealer=dealer,
            product=registered_product,
            address="123 Demo Street, City",
            scheduled_date=timezone.now() + timedelta(days=1),
            status=JobStatus.ASSIGNED
        )
        
    # Request 7: IN_PROGRESS
    print("Creating IN_PROGRESS requests...")
    req_ip = InstallationRequest.objects.create(
        customer=customer,
        dealer=dealer,
        registered_product=registered_product,
        status=InstallationStatus.IN_PROGRESS
    )
    TechnicianJob.objects.create(
        technician=tech1,
        installation_request=req_ip,
        job_type=JobType.INSTALLATION,
        customer=customer,
        dealer=dealer,
        product=registered_product,
        address="456 Active Road",
        scheduled_date=timezone.now(),
        status=JobStatus.IN_PROGRESS
    )
    
    # Request 8: COMPLETED
    print("Creating COMPLETED requests...")
    req_comp = InstallationRequest.objects.create(
        customer=customer,
        dealer=dealer,
        registered_product=registered_product,
        status=InstallationStatus.COMPLETED
    )
    TechnicianJob.objects.create(
        technician=tech2,
        installation_request=req_comp,
        job_type=JobType.INSTALLATION,
        customer=customer,
        dealer=dealer,
        product=registered_product,
        address="789 Done Ave",
        scheduled_date=timezone.now() - timedelta(days=2),
        status=JobStatus.COMPLETED
    )

    print(f"Generated {InstallationRequest.objects.count()} requests successfully!")

generate_demo_data()
