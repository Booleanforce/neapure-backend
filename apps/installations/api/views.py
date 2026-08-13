from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from shared.constants.roles import UserRole
from apps.installations.models import (
    InstallationRequest, InstallationStatus, InstallationHistory,
    InstallationPhoto, PhotoType, InstallationChecklist, InstallationSignature
)
from apps.installations.api.serializers import InstallationRequestSerializer
from apps.accounts.permissions import IsSuperAdmin
from apps.technicians.models import TechnicianJob, JobType, JobStatus
from django.utils.dateparse import parse_datetime
from apps.accounts.models import User

class InstallationRequestViewSet(viewsets.ModelViewSet):
    """
    API for Dealers to request installations, and Admins to approve them.
    """
    serializer_class = InstallationRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["registered_product__serial_number", "customer__email"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]
    filterset_fields = ["status"]

    def get_queryset(self):
        user = self.request.user
        queryset = InstallationRequest.objects.select_related("registered_product", "dealer", "customer")
        
        if user.role == UserRole.DEALER:
            return queryset.filter(dealer=user)
        elif user.role == UserRole.CUSTOMER:
            return queryset.filter(customer=user)
        elif user.role == UserRole.TECHNICIAN:
            # Technicians only see jobs assigned to them
            return queryset.filter(assigned_jobs__technician=user)
        elif user.role in [UserRole.SUPER_ADMIN, UserRole.OPERATIONS_ADMIN]:
            return queryset
            
        return queryset.none()

    def create(self, request, *args, **kwargs):
        # Customers cannot request directly
        if request.user.role == UserRole.CUSTOMER:
            return Response({"error": "Customers cannot request installations directly."}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        dealer = request.user if request.user.role == UserRole.DEALER else None
        
        # We explicitly don't pass status, so it defaults to PENDING_APPROVAL
        instance = serializer.save(dealer=dealer)
        
        InstallationHistory.objects.create(
            installation=instance,
            event_type="REQUEST_SUBMITTED",
            description=f"Installation request submitted by {request.user.role}.",
            performed_by=request.user
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        # Dealers cannot update an existing request, they can only create
        if request.user.role == UserRole.DEALER:
            return Response({"error": "Dealers cannot modify installation requests."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated, IsSuperAdmin])
    def approve(self, request, pk=None):
        instance = self.get_object()
        instance.status = InstallationStatus.APPROVED
        
        admin_notes = request.data.get("admin_notes", "")
        if admin_notes:
            instance.admin_notes = admin_notes
            
        instance.save(update_fields=["status", "admin_notes"])
        
        InstallationHistory.objects.create(
            installation=instance,
            event_type="REQUEST_APPROVED",
            description=f"Installation request approved.",
            performed_by=request.user
        )
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated, IsSuperAdmin])
    def disapprove(self, request, pk=None):
        instance = self.get_object()
        instance.status = InstallationStatus.DISAPPROVED
        
        admin_notes = request.data.get("admin_notes", "")
        if admin_notes:
            instance.admin_notes = admin_notes
            
        instance.save(update_fields=["status", "admin_notes"])
        
        InstallationHistory.objects.create(
            installation=instance,
            event_type="REQUEST_DISAPPROVED",
            description=f"Installation request disapproved.",
            performed_by=request.user
        )
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def assign_technician(self, request, pk=None):
        if request.user.role not in [UserRole.SUPER_ADMIN, UserRole.OPERATIONS_ADMIN]:
            return Response({"error": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
            
        instance = self.get_object()
        
        if instance.status != InstallationStatus.APPROVED and instance.status != InstallationStatus.SCHEDULED:
            return Response({"error": "Request must be APPROVED to assign a technician."}, status=status.HTTP_400_BAD_REQUEST)
            
        technician_id = request.data.get("technician_id")
        scheduled_date_str = request.data.get("scheduled_date")
        address = request.data.get("address")
        
        if not technician_id or not scheduled_date_str or not address:
            return Response({"error": "technician_id, scheduled_date, and address are required."}, status=status.HTTP_400_BAD_REQUEST)
            
        scheduled_date = parse_datetime(scheduled_date_str)
        if not scheduled_date:
            return Response({"error": "Invalid scheduled_date format."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            technician = User.objects.get(id=technician_id, role=UserRole.TECHNICIAN)
        except User.DoesNotExist:
            return Response({"error": "Valid technician not found."}, status=status.HTTP_404_NOT_FOUND)
            
        # Create or update TechnicianJob
        job, created = TechnicianJob.objects.update_or_create(
            installation_request=instance,
            defaults={
                'technician': technician,
                'job_type': JobType.INSTALLATION,
                'customer': instance.customer,
                'dealer': instance.dealer,
                'product': instance.registered_product,
                'address': address,
                'scheduled_date': scheduled_date,
                'status': JobStatus.ASSIGNED
            }
        )
        
        instance.status = InstallationStatus.ASSIGNED
        instance.save(update_fields=["status"])
        
        InstallationHistory.objects.create(
            installation=instance,
            event_type="TECHNICIAN_ASSIGNED",
            description=f"Assigned to technician {technician.email} for {scheduled_date_str}.",
            performed_by=request.user
        )
        
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def reschedule(self, request, pk=None):
        if request.user.role not in [UserRole.SUPER_ADMIN, UserRole.OPERATIONS_ADMIN]:
            return Response({"error": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
            
        instance = self.get_object()
        scheduled_date_str = request.data.get("scheduled_date")
        reason = request.data.get("reason", "No reason provided")
        
        if not scheduled_date_str:
            return Response({"error": "scheduled_date is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        scheduled_date = parse_datetime(scheduled_date_str)
        if not scheduled_date:
            return Response({"error": "Invalid scheduled_date format."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Update TechnicianJob
        job = TechnicianJob.objects.filter(installation_request=instance).first()
        if not job:
            return Response({"error": "No technician job assigned to this request."}, status=status.HTTP_400_BAD_REQUEST)
            
        job.scheduled_date = scheduled_date
        job.save(update_fields=["scheduled_date"])
        
        instance.status = InstallationStatus.RESCHEDULED
        instance.save(update_fields=["status"])
        
        InstallationHistory.objects.create(
            installation=instance,
            event_type="JOB_RESCHEDULED",
            description=f"Rescheduled to {scheduled_date_str}. Reason: {reason}",
            performed_by=request.user
        )
        
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def accept_job(self, request, pk=None):
        if request.user.role != UserRole.TECHNICIAN:
            return Response({"error": "Only technicians can accept jobs."}, status=status.HTTP_403_FORBIDDEN)
            
        instance = self.get_object()
        job = TechnicianJob.objects.filter(installation_request=instance, technician=request.user).first()
        
        if not job:
            return Response({"error": "You are not assigned to this job."}, status=status.HTTP_403_FORBIDDEN)
            
        if instance.status != InstallationStatus.ASSIGNED and instance.status != InstallationStatus.RESCHEDULED:
            return Response({"error": "Job is not in a state to be accepted."}, status=status.HTTP_400_BAD_REQUEST)
            
        instance.status = InstallationStatus.ACCEPTED
        instance.save(update_fields=["status"])
        
        job.status = JobStatus.PENDING # Actually, technician model has ASSIGNED, PENDING, IN_PROGRESS, etc.
        job.save(update_fields=["status"])
        
        InstallationHistory.objects.create(
            installation=instance,
            event_type="JOB_ACCEPTED",
            description=f"Job accepted by technician.",
            performed_by=request.user
        )
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def reject_job(self, request, pk=None):
        if request.user.role != UserRole.TECHNICIAN:
            return Response({"error": "Only technicians can reject jobs."}, status=status.HTTP_403_FORBIDDEN)
            
        instance = self.get_object()
        job = TechnicianJob.objects.filter(installation_request=instance, technician=request.user).first()
        
        if not job:
            return Response({"error": "You are not assigned to this job."}, status=status.HTTP_403_FORBIDDEN)
            
        reason = request.data.get("reason", "No reason provided")
            
        instance.status = InstallationStatus.REJECTED
        instance.save(update_fields=["status"])
        
        # We can either delete the TechnicianJob, or mark it cancelled.
        job.status = JobStatus.CANCELLED
        job.notes = f"Rejected by technician. Reason: {reason}"
        job.save(update_fields=["status", "notes"])
        
        InstallationHistory.objects.create(
            installation=instance,
            event_type="JOB_REJECTED",
            description=f"Job rejected by technician. Reason: {reason}",
            performed_by=request.user
        )
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def check_in(self, request, pk=None):
        if request.user.role != UserRole.TECHNICIAN:
            return Response({"error": "Only technicians can check in."}, status=status.HTTP_403_FORBIDDEN)
            
        instance = self.get_object()
        job = TechnicianJob.objects.filter(installation_request=instance, technician=request.user).first()
        
        if not job:
            return Response({"error": "You are not assigned to this job."}, status=status.HTTP_403_FORBIDDEN)
            
        if instance.status != InstallationStatus.ACCEPTED:
            return Response({"error": "Job must be ACCEPTED before checking in."}, status=status.HTTP_400_BAD_REQUEST)
            
        instance.status = InstallationStatus.IN_PROGRESS
        instance.save(update_fields=["status"])
        
        job.status = JobStatus.IN_PROGRESS
        job.save(update_fields=["status"])
        
        location = request.data.get("location", "Location not provided")
        
        InstallationHistory.objects.create(
            installation=instance,
            event_type="TECHNICIAN_CHECK_IN",
            description=f"Technician checked in at {location}.",
            performed_by=request.user
        )
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def check_out(self, request, pk=None):
        if request.user.role != UserRole.TECHNICIAN:
            return Response({"error": "Only technicians can check out."}, status=status.HTTP_403_FORBIDDEN)
            
        instance = self.get_object()
        job = TechnicianJob.objects.filter(installation_request=instance, technician=request.user).first()
        
        if not job:
            return Response({"error": "You are not assigned to this job."}, status=status.HTTP_403_FORBIDDEN)
            
        if instance.status != InstallationStatus.IN_PROGRESS:
            return Response({"error": "Job must be IN_PROGRESS before checking out."}, status=status.HTTP_400_BAD_REQUEST)
            
        # We don't mark as COMPLETED here. That requires a specific `complete` action that validates photos and checklist.
        location = request.data.get("location", "Location not provided")
        notes = request.data.get("notes", "")
        
        InstallationHistory.objects.create(
            installation=instance,
            event_type="TECHNICIAN_CHECK_OUT",
            description=f"Technician checked out from {location}. Notes: {notes}",
            performed_by=request.user
        )
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def upload_photos(self, request, pk=None):
        if request.user.role != UserRole.TECHNICIAN:
            return Response({"error": "Only technicians can upload photos."}, status=status.HTTP_403_FORBIDDEN)
            
        instance = self.get_object()
        job = TechnicianJob.objects.filter(installation_request=instance, technician=request.user).first()
        
        if not job:
            return Response({"error": "You are not assigned to this job."}, status=status.HTTP_403_FORBIDDEN)
            
        if instance.status not in [InstallationStatus.IN_PROGRESS, InstallationStatus.ACCEPTED]:
            return Response({"error": "Job must be ACCEPTED or IN_PROGRESS."}, status=status.HTTP_400_BAD_REQUEST)
            
        photo_type = request.data.get("photo_type")
        photo = request.FILES.get("photo")
        
        if not photo_type or photo_type not in [PhotoType.BEFORE, PhotoType.AFTER]:
            return Response({"error": "photo_type must be BEFORE or AFTER."}, status=status.HTTP_400_BAD_REQUEST)
            
        if not photo:
            return Response({"error": "photo file is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        InstallationPhoto.objects.create(
            installation=instance,
            photo_type=photo_type,
            photo=photo,
            uploaded_by=request.user
        )
        
        InstallationHistory.objects.create(
            installation=instance,
            event_type="PHOTO_UPLOADED",
            description=f"Technician uploaded a {photo_type} photo.",
            performed_by=request.user
        )
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def checklist(self, request, pk=None):
        if request.user.role != UserRole.TECHNICIAN:
            return Response({"error": "Only technicians can submit the checklist."}, status=status.HTTP_403_FORBIDDEN)
            
        instance = self.get_object()
        job = TechnicianJob.objects.filter(installation_request=instance, technician=request.user).first()
        
        if not job:
            return Response({"error": "You are not assigned to this job."}, status=status.HTTP_403_FORBIDDEN)
            
        if instance.status != InstallationStatus.IN_PROGRESS:
            return Response({"error": "Job must be IN_PROGRESS."}, status=status.HTTP_400_BAD_REQUEST)
            
        data = request.data.get("data")
        if not data or not isinstance(data, dict):
            return Response({"error": "Checklist 'data' (JSON object) is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        checklist, created = InstallationChecklist.objects.update_or_create(
            installation=instance,
            defaults={
                'data': data,
                'submitted_by': request.user
            }
        )
        
        InstallationHistory.objects.create(
            installation=instance,
            event_type="CHECKLIST_SUBMITTED",
            description=f"Technician submitted the installation checklist.",
            performed_by=request.user
        )
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def signature(self, request, pk=None):
        if request.user.role != UserRole.TECHNICIAN:
            return Response({"error": "Only technicians can submit the signature."}, status=status.HTTP_403_FORBIDDEN)
            
        instance = self.get_object()
        job = TechnicianJob.objects.filter(installation_request=instance, technician=request.user).first()
        
        if not job:
            return Response({"error": "You are not assigned to this job."}, status=status.HTTP_403_FORBIDDEN)
            
        if instance.status != InstallationStatus.IN_PROGRESS:
            return Response({"error": "Job must be IN_PROGRESS."}, status=status.HTTP_400_BAD_REQUEST)
            
        signature_image = request.FILES.get("signature_image")
        if not signature_image:
            return Response({"error": "signature_image file is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        InstallationSignature.objects.update_or_create(
            installation=instance,
            defaults={
                'signature_image': signature_image,
                'collected_by': request.user
            }
        )
        
        InstallationHistory.objects.create(
            installation=instance,
            event_type="SIGNATURE_COLLECTED",
            description=f"Technician collected customer signature.",
            performed_by=request.user
        )
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        if request.user.role != UserRole.TECHNICIAN:
            return Response({"error": "Only technicians can complete jobs."}, status=status.HTTP_403_FORBIDDEN)
            
        instance = self.get_object()
        job = TechnicianJob.objects.filter(installation_request=instance, technician=request.user).first()
        
        if not job:
            return Response({"error": "You are not assigned to this job."}, status=status.HTTP_403_FORBIDDEN)
            
        if instance.status != InstallationStatus.IN_PROGRESS:
            return Response({"error": "Job must be IN_PROGRESS."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Validation checks
        if not hasattr(instance, 'checklist'):
            return Response({"error": "Installation checklist is required before completing."}, status=status.HTTP_400_BAD_REQUEST)
        if not hasattr(instance, 'signature'):
            return Response({"error": "Customer signature is required before completing."}, status=status.HTTP_400_BAD_REQUEST)
        if not instance.photos.filter(photo_type=PhotoType.BEFORE).exists():
            return Response({"error": "At least one BEFORE photo is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not instance.photos.filter(photo_type=PhotoType.AFTER).exists():
            return Response({"error": "At least one AFTER photo is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        from django.utils import timezone
        
        instance.status = InstallationStatus.COMPLETED
        instance.save(update_fields=["status"])
        
        job.status = JobStatus.COMPLETED
        job.completion_date = timezone.now()
        job.save(update_fields=["status", "completion_date"])
        
        InstallationHistory.objects.create(
            installation=instance,
            event_type="JOB_COMPLETED",
            description=f"Installation job completed successfully by technician.",
            performed_by=request.user
        )
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def report(self, request, pk=None):
        instance = self.get_object()
        
        # Ensure only authorized people can view the report
        if request.user.role not in [UserRole.SUPER_ADMIN, UserRole.OPERATIONS_ADMIN]:
            # Technician can view their own reports
            if request.user.role == UserRole.TECHNICIAN:
                if not TechnicianJob.objects.filter(installation_request=instance, technician=request.user).exists():
                    return Response({"error": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
            # Dealer can view their own reports
            elif request.user.role == UserRole.DEALER and instance.dealer != request.user:
                return Response({"error": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
            # Customer can view their own reports
            elif request.user.role == UserRole.CUSTOMER and instance.customer != request.user:
                return Response({"error": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        
        return Response(self.get_serializer(instance).data)

from apps.installations.models import ReplacementKitRequest
from apps.installations.api.serializers import ReplacementKitRequestSerializer

class ReplacementKitRequestViewSet(viewsets.ModelViewSet):
    """
    API for Dealers to request replacement kits, and Admins to manage them.
    """
    serializer_class = ReplacementKitRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["registered_product__serial_number", "customer__email", "description"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]
    filterset_fields = ["status"]

    def get_queryset(self):
        user = self.request.user
        queryset = ReplacementKitRequest.objects.select_related("registered_product", "dealer", "customer")
        
        if user.role == UserRole.DEALER:
            return queryset.filter(dealer=user)
        elif user.role == UserRole.CUSTOMER:
            return queryset.filter(customer=user)
        elif user.role in [UserRole.SUPER_ADMIN, UserRole.OPERATIONS_ADMIN]:
            return queryset
            
        return queryset.none()

    def create(self, request, *args, **kwargs):
        if request.user.role == UserRole.CUSTOMER:
            return Response({"error": "Customers cannot request replacement kits directly."}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        dealer = request.user if request.user.role == UserRole.DEALER else None
        
        serializer.save(
            dealer=dealer,
            status=InstallationStatus.PENDING
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        if request.user.role == UserRole.DEALER:
            return Response({"error": "Dealers cannot modify replacement kit requests."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated, IsSuperAdmin])
    def approve(self, request, pk=None):
        instance = self.get_object()
        instance.status = InstallationStatus.APPROVED
        admin_notes = request.data.get("admin_notes", "")
        if admin_notes:
            instance.admin_notes = admin_notes
        instance.save(update_fields=["status", "admin_notes"])
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated, IsSuperAdmin])
    def disapprove(self, request, pk=None):
        instance = self.get_object()
        instance.status = InstallationStatus.DISAPPROVED
        admin_notes = request.data.get("admin_notes", "")
        if admin_notes:
            instance.admin_notes = admin_notes
        instance.save(update_fields=["status", "admin_notes"])
        return Response(self.get_serializer(instance).data)
