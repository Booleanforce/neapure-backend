from django.db import models
from shared.mixins.base import BaseModel
from shared.mixins.soft_delete import SoftDeleteModel
from apps.accounts.models import User

class Region(models.TextChoices):
    DHAKA_NORTH = "DHAKA_NORTH", "Dhaka North"
    DHAKA_SOUTH = "DHAKA_SOUTH", "Dhaka South"
    CHATTOGRAM = "CHATTOGRAM", "Chattogram"
    SYLHET = "SYLHET", "Sylhet"

class TechnicianStatus(models.TextChoices):
    AVAILABLE = "AVAILABLE", "Available"
    BUSY = "BUSY", "Busy"
    ON_JOB = "ON_JOB", "On Job"
    ON_LEAVE = "ON_LEAVE", "On Leave"
    OFFLINE = "OFFLINE", "Offline"

class TechnicianProfile(SoftDeleteModel, BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="technician_profile"
    )
    region = models.CharField(
        max_length=50,
        choices=Region.choices,
        blank=True,
        default=""
    )
    skills = models.JSONField(
        default=list,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=TechnicianStatus.choices,
        default=TechnicianStatus.AVAILABLE
    )
    profile_photo = models.ImageField(
        upload_to="technicians/profile/",
        blank=True,
        null=True,
    )
        
    
    class Meta:
        db_table = "technician_profiles"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - Technician Profile"

class JobType(models.TextChoices):
    INSTALLATION = "INSTALLATION", "Installation"
    SERVICE = "SERVICE", "Service"

class JobPriority(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    URGENT = "URGENT", "Urgent"

class JobStatus(models.TextChoices):
    ASSIGNED = "ASSIGNED", "Assigned"
    PENDING = "PENDING", "Pending"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"

class TechnicianJob(SoftDeleteModel, BaseModel):
    technician = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assigned_jobs")
    job_type = models.CharField(max_length=20, choices=JobType.choices)
    
    installation_request = models.ForeignKey(
        'installations.InstallationRequest', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="assigned_jobs"
    )
    replacement_kit_request = models.ForeignKey(
        'installations.ReplacementKitRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_jobs"
    )
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="customer_jobs")
    dealer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="dealer_jobs")
    product = models.ForeignKey('products.RegisteredProduct', on_delete=models.SET_NULL, null=True, blank=True)
    
    address = models.TextField()
    scheduled_date = models.DateTimeField()
    priority = models.CharField(max_length=20, choices=JobPriority.choices, default=JobPriority.MEDIUM)
    notes = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=JobStatus.choices, default=JobStatus.ASSIGNED)
    
    completion_date = models.DateTimeField(null=True, blank=True)
    customer_rating = models.IntegerField(null=True, blank=True)
    customer_feedback = models.TextField(blank=True, default="")

    class Meta:
        db_table = "technician_jobs"
        ordering = ["-scheduled_date"]

    def __str__(self):
        return f"Job {self.id} for {self.technician.email}"
