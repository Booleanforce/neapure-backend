from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from shared.constants.roles import UserRole

from apps.installations.models import (
    InstallationRequest,
    InstallationStatus,
    InstallationHistory,
    InstallationPhoto,
    PhotoType,
    InstallationChecklist,
    InstallationSignature,
    ReplacementKitRequest,
)

from apps.installations.api.serializers import (
    InstallationRequestSerializer,
    ReplacementKitRequestSerializer,
)

from apps.accounts.permissions import IsSuperAdmin
from apps.accounts.models import User

from apps.technicians.models import (
    TechnicianJob,
    JobType,
    JobStatus,
)


# ============================================================================
# INSTALLATION REQUEST VIEWSET
# ============================================================================


class InstallationRequestViewSet(viewsets.ModelViewSet):
    """
    API for Dealers to request installations
    and Admins to manage installation requests.
    """

    serializer_class = InstallationRequestSerializer

    permission_classes = [
        IsAuthenticated
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = [
        "registered_product__serial_number",
        "customer__email",
    ]

    ordering_fields = [
        "created_at",
    ]

    ordering = [
        "-created_at",
    ]

    filterset_fields = [
        "status",
    ]

    # ========================================================================
    # QUERYSET
    # ========================================================================

    def get_queryset(self):
        user = self.request.user

        queryset = InstallationRequest.objects.select_related(
            "registered_product",
            "dealer",
            "customer",
        )

        # =========================================================
        # ROLE BASED FILTERING
        # =========================================================

        if user.role == UserRole.DEALER:
            queryset = queryset.filter(dealer=user)

        elif user.role == UserRole.CUSTOMER:
            queryset = queryset.filter(customer=user)

        elif user.role == UserRole.TECHNICIAN:
            queryset = queryset.filter(
                assigned_jobs__technician=user
            )

        elif user.role in [
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_ADMIN,
        ]:
            pass

        else:
            return queryset.none()

        # =========================================================
        # STATUS GROUP FILTER
        # =========================================================

        status_group = self.request.query_params.get(
            "status_group"
        )

        if status_group == "pending":
            queryset = queryset.filter(
                status=InstallationStatus.PENDING_APPROVAL
            )

        elif status_group == "active":
            queryset = queryset.filter(
                status__in=[
                    InstallationStatus.APPROVED,
                    InstallationStatus.SCHEDULED,
                    InstallationStatus.ASSIGNED,
                    InstallationStatus.ACCEPTED,
                    InstallationStatus.RESCHEDULED,
                    InstallationStatus.IN_PROGRESS,
                ]
            )

        elif status_group == "completed":
            queryset = queryset.filter(
                status=InstallationStatus.COMPLETED
            )

        # ALL = no additional filtering

        return queryset

    # ========================================================================
    # CREATE
    # ========================================================================

    def create(
        self,
        request,
        *args,
        **kwargs,
    ):

        # Customers cannot create installation requests
        if request.user.role == UserRole.CUSTOMER:

            return Response(
                {
                    "success": False,
                    "error": (
                        "Customers cannot request "
                        "installations directly."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        dealer = (
            request.user
            if request.user.role == UserRole.DEALER
            else None
        )

        instance = serializer.save(
            dealer=dealer
        )

        InstallationHistory.objects.create(
            installation=instance,
            event_type="REQUEST_SUBMITTED",
            description=(
                f"Installation request submitted "
                f"by {request.user.role}."
            ),
            performed_by=request.user,
        )

        return Response(
            self.get_serializer(instance).data,
            status=status.HTTP_201_CREATED,
        )

    # ========================================================================
    # UPDATE
    # ========================================================================

    def update(
        self,
        request,
        *args,
        **kwargs,
    ):

        if request.user.role == UserRole.DEALER:

            return Response(
                {
                    "success": False,
                    "error": (
                        "Dealers cannot modify "
                        "installation requests."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().update(
            request,
            *args,
            **kwargs,
        )

    # ========================================================================
    # DELETE
    # ========================================================================

    def destroy(
        self,
        request,
        *args,
        **kwargs,
    ):
        """
        Permanently delete an installation request.

        Only SUPER_ADMIN and OPERATIONS_ADMIN
        can delete installation requests.
        """

        # --------------------------------------------------------------------
        # Permission
        # --------------------------------------------------------------------

        if request.user.role not in [
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_ADMIN,
        ]:

            return Response(
                {
                    "success": False,
                    "error": (
                        "You do not have permission "
                        "to delete installation requests."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # --------------------------------------------------------------------
        # Get object
        # --------------------------------------------------------------------

        try:

            instance = self.get_object()

        except Exception:

            return Response(
                {
                    "success": False,
                    "error": (
                        "Installation request "
                        "not found."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        request_id = str(
            instance.id
        )

        # --------------------------------------------------------------------
        # Permanent deletion
        # --------------------------------------------------------------------

        try:

            with transaction.atomic():

                # ============================================================
                # Delete Technician Jobs
                # ============================================================

                TechnicianJob.objects.filter(
                    installation_request=instance
                ).delete()

                # ============================================================
                # Delete Installation History
                # ============================================================

                InstallationHistory.objects.filter(
                    installation=instance
                ).delete()

                # ============================================================
                # Delete Installation Photos
                # ============================================================

                InstallationPhoto.objects.filter(
                    installation=instance
                ).delete()

                # ============================================================
                # Delete Checklist
                # ============================================================

                InstallationChecklist.objects.filter(
                    installation=instance
                ).delete()

                # ============================================================
                # Delete Signature
                # ============================================================

                InstallationSignature.objects.filter(
                    installation=instance
                ).delete()

                # ============================================================
                # HARD DELETE INSTALLATION REQUEST
                # ============================================================

                instance.hard_delete()

            return Response(
                {
                    "success": True,
                    "message": (
                        "Installation request "
                        "deleted successfully."
                    ),
                    "id": request_id,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:

            import traceback

            traceback.print_exc()

            return Response(
                {
                    "success": False,
                    "message": (
                        "Failed to delete "
                        "installation request."
                    ),
                    "error": str(exc),
                    "id": request_id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    # ========================================================================
    # STATISTICS
    # ========================================================================

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[
            IsAuthenticated
        ],
        url_path="statistics",
    )
    def statistics(
        self,
        request,
    ):
        """
        Return installation statistics.

        Statistics are calculated from the same queryset
        the authenticated user is allowed to access.
        """

        queryset = self.get_queryset()

        # --------------------------------------------------------------------
        # Total
        # --------------------------------------------------------------------

        total = queryset.count()

        # --------------------------------------------------------------------
        # Pending
        # --------------------------------------------------------------------

        pending = queryset.filter(
            status=InstallationStatus.PENDING_APPROVAL
        ).count()

        # --------------------------------------------------------------------
        # Active
        # --------------------------------------------------------------------

        active = queryset.filter(
            status__in=[
                InstallationStatus.APPROVED,
                InstallationStatus.SCHEDULED,
                InstallationStatus.ASSIGNED,
                InstallationStatus.ACCEPTED,
                InstallationStatus.RESCHEDULED,
                InstallationStatus.IN_PROGRESS,
            ]
        ).count()

        # --------------------------------------------------------------------
        # Completed
        # --------------------------------------------------------------------

        completed = queryset.filter(
            status=InstallationStatus.COMPLETED
        ).count()

        return Response(
            {
                "total": total,
                "pending": pending,
                "active": active,
                "completed": completed,
            },
            status=status.HTTP_200_OK,
        )

    # ========================================================================
    # APPROVE
    # ========================================================================

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[
            IsAuthenticated,
            IsSuperAdmin,
        ],
    )
    def approve(
        self,
        request,
        pk=None,
    ):

        instance = self.get_object()

        instance.status = (
            InstallationStatus.APPROVED
        )

        admin_notes = request.data.get(
            "admin_notes",
            "",
        )

        if admin_notes:

            instance.admin_notes = admin_notes

        instance.save(
            update_fields=[
                "status",
                "admin_notes",
            ]
        )

        InstallationHistory.objects.create(
            installation=instance,
            event_type="REQUEST_APPROVED",
            description=(
                "Installation request approved."
            ),
            performed_by=request.user,
        )

        return Response(
            self.get_serializer(instance).data
        )

    # ========================================================================
    # DISAPPROVE
    # ========================================================================

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[
            IsAuthenticated,
            IsSuperAdmin,
        ],
    )
    def disapprove(
        self,
        request,
        pk=None,
    ):

        instance = self.get_object()

        instance.status = (
            InstallationStatus.DISAPPROVED
        )

        admin_notes = request.data.get(
            "admin_notes",
            "",
        )

        if admin_notes:

            instance.admin_notes = admin_notes

        instance.save(
            update_fields=[
                "status",
                "admin_notes",
            ]
        )

        InstallationHistory.objects.create(
            installation=instance,
            event_type="REQUEST_DISAPPROVED",
            description=(
                "Installation request disapproved."
            ),
            performed_by=request.user,
        )

        return Response(
            self.get_serializer(instance).data
        )

    # ========================================================================
    # ASSIGN TECHNICIAN
    # ========================================================================

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated
        ],
    )
    def assign_technician(
        self,
        request,
        pk=None,
    ):

        if request.user.role not in [
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_ADMIN,
        ]:

            return Response(
                {
                    "error": "Unauthorized."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = self.get_object()

        if instance.status not in [
            InstallationStatus.APPROVED,
            InstallationStatus.SCHEDULED,
        ]:

            return Response(
                {
                    "error": (
                        "Request must be APPROVED "
                        "or SCHEDULED to assign "
                        "a technician."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        technician_id = request.data.get(
            "technician_id"
        )

        scheduled_date_str = request.data.get(
            "scheduled_date"
        )

        address = request.data.get(
            "address"
        )

        if not technician_id or not scheduled_date_str or not address:

            return Response(
                {
                    "error": (
                        "technician_id, scheduled_date, "
                        "and address are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        scheduled_date = parse_datetime(
            scheduled_date_str
        )

        if not scheduled_date:

            return Response(
                {
                    "error": (
                        "Invalid scheduled_date format."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            technician = User.objects.get(
                id=technician_id,
                role=UserRole.TECHNICIAN,
            )

        except User.DoesNotExist:

            return Response(
                {
                    "error": (
                        "Valid technician not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # --------------------------------------------------------------------
        # Create / update technician job
        # --------------------------------------------------------------------

        job, created = TechnicianJob.objects.update_or_create(
            installation_request=instance,
            defaults={
                "technician": technician,
                "job_type": JobType.INSTALLATION,
                "customer": instance.customer,
                "dealer": instance.dealer,
                "product": instance.registered_product,
                "address": address,
                "scheduled_date": scheduled_date,
                "status": JobStatus.ASSIGNED,
            },
        )

        instance.status = (
            InstallationStatus.ASSIGNED
        )

        instance.save(
            update_fields=["status"]
        )

        InstallationHistory.objects.create(
            installation=instance,
            event_type="TECHNICIAN_ASSIGNED",
            description=(
                f"Assigned to technician "
                f"{technician.email} for "
                f"{scheduled_date_str}."
            ),
            performed_by=request.user,
        )

        return Response(
            self.get_serializer(instance).data
        )

    # ========================================================================
    # RESCHEDULE
    # ========================================================================

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated
        ],
    )
    def reschedule(
        self,
        request,
        pk=None,
    ):

        if request.user.role not in [
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_ADMIN,
        ]:

            return Response(
                {
                    "error": "Unauthorized."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = self.get_object()

        scheduled_date_str = request.data.get(
            "scheduled_date"
        )

        reason = request.data.get(
            "reason",
            "No reason provided",
        )

        if not scheduled_date_str:

            return Response(
                {
                    "error": (
                        "scheduled_date is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        scheduled_date = parse_datetime(
            scheduled_date_str
        )

        if not scheduled_date:

            return Response(
                {
                    "error": (
                        "Invalid scheduled_date format."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        job = TechnicianJob.objects.filter(
            installation_request=instance
        ).first()

        if not job:

            return Response(
                {
                    "error": (
                        "No technician job assigned "
                        "to this request."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        job.scheduled_date = scheduled_date

        job.save(
            update_fields=[
                "scheduled_date"
            ]
        )

        instance.status = (
            InstallationStatus.RESCHEDULED
        )

        instance.save(
            update_fields=["status"]
        )

        InstallationHistory.objects.create(
            installation=instance,
            event_type="JOB_RESCHEDULED",
            description=(
                f"Rescheduled to "
                f"{scheduled_date_str}. "
                f"Reason: {reason}"
            ),
            performed_by=request.user,
        )

        return Response(
            self.get_serializer(instance).data
        )

    # ========================================================================
    # ACCEPT JOB
    # ========================================================================

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated
        ],
    )
    def accept_job(
        self,
        request,
        pk=None,
    ):

        if request.user.role != UserRole.TECHNICIAN:

            return Response(
                {
                    "error": (
                        "Only technicians "
                        "can accept jobs."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = self.get_object()

        job = TechnicianJob.objects.filter(
            installation_request=instance,
            technician=request.user,
        ).first()

        if not job:

            return Response(
                {
                    "error": (
                        "You are not assigned "
                        "to this job."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if instance.status not in [
            InstallationStatus.ASSIGNED,
            InstallationStatus.RESCHEDULED,
        ]:

            return Response(
                {
                    "error": (
                        "Job is not in a state "
                        "to be accepted."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.status = (
            InstallationStatus.ACCEPTED
        )

        instance.save(
            update_fields=["status"]
        )

        job.status = JobStatus.PENDING

        job.save(
            update_fields=["status"]
        )

        InstallationHistory.objects.create(
            installation=instance,
            event_type="JOB_ACCEPTED",
            description=(
                "Job accepted by technician."
            ),
            performed_by=request.user,
        )

        return Response(
            self.get_serializer(instance).data
        )

    # ========================================================================
    # REJECT JOB
    # ========================================================================

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated
        ],
    )
    def reject_job(
        self,
        request,
        pk=None,
    ):

        if request.user.role != UserRole.TECHNICIAN:

            return Response(
                {
                    "error": (
                        "Only technicians "
                        "can reject jobs."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = self.get_object()

        job = TechnicianJob.objects.filter(
            installation_request=instance,
            technician=request.user,
        ).first()

        if not job:

            return Response(
                {
                    "error": (
                        "You are not assigned "
                        "to this job."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        reason = request.data.get(
            "reason",
            "No reason provided",
        )

        instance.status = (
            InstallationStatus.REJECTED
        )

        instance.save(
            update_fields=["status"]
        )

        job.status = JobStatus.CANCELLED

        job.notes = (
            f"Rejected by technician. "
            f"Reason: {reason}"
        )

        job.save(
            update_fields=[
                "status",
                "notes",
            ]
        )

        InstallationHistory.objects.create(
            installation=instance,
            event_type="JOB_REJECTED",
            description=(
                f"Job rejected by technician. "
                f"Reason: {reason}"
            ),
            performed_by=request.user,
        )

        return Response(
            self.get_serializer(instance).data
        )

    # ========================================================================
    # CHECK IN
    # ========================================================================

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated
        ],
    )
    def check_in(
        self,
        request,
        pk=None,
    ):

        if request.user.role != UserRole.TECHNICIAN:

            return Response(
                {
                    "error": (
                        "Only technicians "
                        "can check in."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = self.get_object()

        job = TechnicianJob.objects.filter(
            installation_request=instance,
            technician=request.user,
        ).first()

        if not job:

            return Response(
                {
                    "error": (
                        "You are not assigned "
                        "to this job."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if instance.status != InstallationStatus.ACCEPTED:

            return Response(
                {
                    "error": (
                        "Job must be ACCEPTED "
                        "before checking in."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.status = (
            InstallationStatus.IN_PROGRESS
        )

        instance.save(
            update_fields=["status"]
        )

        job.status = JobStatus.IN_PROGRESS

        job.save(
            update_fields=["status"]
        )

        location = request.data.get(
            "location",
            "Location not provided",
        )

        InstallationHistory.objects.create(
            installation=instance,
            event_type="TECHNICIAN_CHECK_IN",
            description=(
                f"Technician checked in "
                f"at {location}."
            ),
            performed_by=request.user,
        )

        return Response(
            self.get_serializer(instance).data
        )

    # ========================================================================
    # CHECK OUT
    # ========================================================================

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated
        ],
    )
    def check_out(
        self,
        request,
        pk=None,
    ):

        if request.user.role != UserRole.TECHNICIAN:

            return Response(
                {
                    "error": (
                        "Only technicians "
                        "can check out."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = self.get_object()

        job = TechnicianJob.objects.filter(
            installation_request=instance,
            technician=request.user,
        ).first()

        if not job:

            return Response(
                {
                    "error": (
                        "You are not assigned "
                        "to this job."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if instance.status != InstallationStatus.IN_PROGRESS:

            return Response(
                {
                    "error": (
                        "Job must be IN_PROGRESS "
                        "before checking out."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        location = request.data.get(
            "location",
            "Location not provided",
        )

        notes = request.data.get(
            "notes",
            "",
        )

        InstallationHistory.objects.create(
            installation=instance,
            event_type="TECHNICIAN_CHECK_OUT",
            description=(
                f"Technician checked out "
                f"from {location}. "
                f"Notes: {notes}"
            ),
            performed_by=request.user,
        )

        return Response(
            self.get_serializer(instance).data
        )

    # ========================================================================
    # UPLOAD PHOTOS
    # ========================================================================

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated
        ],
    )
    def upload_photos(
        self,
        request,
        pk=None,
    ):

        if request.user.role != UserRole.TECHNICIAN:

            return Response(
                {
                    "error": (
                        "Only technicians "
                        "can upload photos."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = self.get_object()

        job = TechnicianJob.objects.filter(
            installation_request=instance,
            technician=request.user,
        ).first()

        if not job:

            return Response(
                {
                    "error": (
                        "You are not assigned "
                        "to this job."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if instance.status not in [
            InstallationStatus.ACCEPTED,
            InstallationStatus.IN_PROGRESS,
        ]:

            return Response(
                {
                    "error": (
                        "Job must be ACCEPTED "
                        "or IN_PROGRESS."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        photo_type = request.data.get(
            "photo_type"
        )

        photo = request.FILES.get(
            "photo"
        )

        if photo_type not in [
            PhotoType.BEFORE,
            PhotoType.AFTER,
        ]:

            return Response(
                {
                    "error": (
                        "photo_type must be "
                        "BEFORE or AFTER."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not photo:

            return Response(
                {
                    "error": (
                        "photo file is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        InstallationPhoto.objects.create(
            installation=instance,
            photo_type=photo_type,
            photo=photo,
            uploaded_by=request.user,
        )

        InstallationHistory.objects.create(
            installation=instance,
            event_type="PHOTO_UPLOADED",
            description=(
                f"Technician uploaded a "
                f"{photo_type} photo."
            ),
            performed_by=request.user,
        )

        return Response(
            self.get_serializer(instance).data
        )

    # ========================================================================
    # CHECKLIST
    # ========================================================================

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated
        ],
    )
    def checklist(
        self,
        request,
        pk=None,
    ):

        if request.user.role != UserRole.TECHNICIAN:

            return Response(
                {
                    "error": (
                        "Only technicians can "
                        "submit the checklist."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = self.get_object()

        job = TechnicianJob.objects.filter(
            installation_request=instance,
            technician=request.user,
        ).first()

        if not job:

            return Response(
                {
                    "error": (
                        "You are not assigned "
                        "to this job."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if instance.status != InstallationStatus.IN_PROGRESS:

            return Response(
                {
                    "error": (
                        "Job must be IN_PROGRESS."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data.get(
            "data"
        )

        if not data or not isinstance(data, dict):

            return Response(
                {
                    "error": (
                        "Checklist 'data' "
                        "(JSON object) is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        InstallationChecklist.objects.update_or_create(
            installation=instance,
            defaults={
                "data": data,
                "submitted_by": request.user,
            },
        )

        InstallationHistory.objects.create(
            installation=instance,
            event_type="CHECKLIST_SUBMITTED",
            description=(
                "Technician submitted "
                "the installation checklist."
            ),
            performed_by=request.user,
        )

        return Response(
            self.get_serializer(instance).data
        )

    # ========================================================================
    # SIGNATURE
    # ========================================================================

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated
        ],
    )
    def signature(
        self,
        request,
        pk=None,
    ):

        if request.user.role != UserRole.TECHNICIAN:

            return Response(
                {
                    "error": (
                        "Only technicians can "
                        "submit the signature."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = self.get_object()

        job = TechnicianJob.objects.filter(
            installation_request=instance,
            technician=request.user,
        ).first()

        if not job:

            return Response(
                {
                    "error": (
                        "You are not assigned "
                        "to this job."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if instance.status != InstallationStatus.IN_PROGRESS:

            return Response(
                {
                    "error": (
                        "Job must be IN_PROGRESS."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        signature_image = request.FILES.get(
            "signature_image"
        )

        if not signature_image:

            return Response(
                {
                    "error": (
                        "signature_image "
                        "file is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        InstallationSignature.objects.update_or_create(
            installation=instance,
            defaults={
                "signature_image": signature_image,
                "collected_by": request.user,
            },
        )

        InstallationHistory.objects.create(
            installation=instance,
            event_type="SIGNATURE_COLLECTED",
            description=(
                "Technician collected "
                "customer signature."
            ),
            performed_by=request.user,
        )

        return Response(
            self.get_serializer(instance).data
        )

    # ========================================================================
    # COMPLETE
    # ========================================================================

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated
        ],
    )
    def complete(
        self,
        request,
        pk=None,
    ):

        if request.user.role != UserRole.TECHNICIAN:

            return Response(
                {
                    "error": (
                        "Only technicians "
                        "can complete jobs."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = self.get_object()

        job = TechnicianJob.objects.filter(
            installation_request=instance,
            technician=request.user,
        ).first()

        if not job:

            return Response(
                {
                    "error": (
                        "You are not assigned "
                        "to this job."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if instance.status != InstallationStatus.IN_PROGRESS:

            return Response(
                {
                    "error": (
                        "Job must be IN_PROGRESS."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------------------------
        # Checklist
        # --------------------------------------------------------------------

        if not hasattr(
            instance,
            "checklist",
        ):

            return Response(
                {
                    "error": (
                        "Installation checklist "
                        "is required before completing."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------------------------
        # Signature
        # --------------------------------------------------------------------

        if not hasattr(
            instance,
            "signature",
        ):

            return Response(
                {
                    "error": (
                        "Customer signature "
                        "is required before completing."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------------------------
        # Before photo
        # --------------------------------------------------------------------

        if not instance.photos.filter(
            photo_type=PhotoType.BEFORE
        ).exists():

            return Response(
                {
                    "error": (
                        "At least one BEFORE "
                        "photo is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------------------------
        # After photo
        # --------------------------------------------------------------------

        if not instance.photos.filter(
            photo_type=PhotoType.AFTER
        ).exists():

            return Response(
                {
                    "error": (
                        "At least one AFTER "
                        "photo is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------------------------
        # Complete
        # --------------------------------------------------------------------

        instance.status = (
            InstallationStatus.COMPLETED
        )

        instance.save(
            update_fields=["status"]
        )

        job.status = JobStatus.COMPLETED

        job.completion_date = timezone.now()

        job.save(
            update_fields=[
                "status",
                "completion_date",
            ]
        )

        InstallationHistory.objects.create(
            installation=instance,
            event_type="JOB_COMPLETED",
            description=(
                "Installation job completed "
                "successfully by technician."
            ),
            performed_by=request.user,
        )

        return Response(
            self.get_serializer(instance).data
        )

    # ========================================================================
    # REPORT
    # ========================================================================

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[
            IsAuthenticated
        ],
    )
    def report(
        self,
        request,
        pk=None,
    ):

        instance = self.get_object()

        # Admin
        if request.user.role in [
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_ADMIN,
        ]:

            return Response(
                self.get_serializer(instance).data
            )

        # Technician
        if request.user.role == UserRole.TECHNICIAN:

            if not TechnicianJob.objects.filter(
                installation_request=instance,
                technician=request.user,
            ).exists():

                return Response(
                    {
                        "error": "Unauthorized."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Dealer
        elif request.user.role == UserRole.DEALER:

            if instance.dealer != request.user:

                return Response(
                    {
                        "error": "Unauthorized."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Customer
        elif request.user.role == UserRole.CUSTOMER:

            if instance.customer != request.user:

                return Response(
                    {
                        "error": "Unauthorized."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        return Response(
            self.get_serializer(instance).data
        )


# ============================================================================
# REPLACEMENT KIT REQUEST VIEWSET
# ============================================================================


class ReplacementKitRequestViewSet(
    viewsets.ModelViewSet
):
    """
    API for Dealers to request replacement kits
    and Admins to manage them.
    """

    serializer_class = (
        ReplacementKitRequestSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = [
        "registered_product__serial_number",
        "customer__email",
        "description",
    ]

    ordering_fields = [
        "created_at",
    ]

    ordering = [
        "-created_at",
    ]

    filterset_fields = [
        "status",
    ]

    # ========================================================================
    # QUERYSET
    # ========================================================================

    def get_queryset(self):

        user = self.request.user

        queryset = (
            ReplacementKitRequest.objects
            .select_related(
                "registered_product",
                "dealer",
                "customer",
            )
            .filter(is_deleted=False)
        )

        if user.role == UserRole.DEALER:

            return queryset.filter(
                dealer=user
            )

        elif user.role == UserRole.CUSTOMER:

            return queryset.filter(
                customer=user
            )

        elif user.role in [
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_ADMIN,
        ]:

            return queryset

        return queryset.none()

    # ========================================================================
    # CREATE
    # ========================================================================

    def create(
        self,
        request,
        *args,
        **kwargs,
    ):

        if request.user.role == UserRole.CUSTOMER:

            return Response(
                {
                    "success": False,
                    "error": (
                        "Customers cannot request "
                        "replacement kits directly."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        dealer = (
            request.user
            if request.user.role == UserRole.DEALER
            else None
        )

        serializer.save(
            dealer=dealer,
            status=InstallationStatus.PENDING_APPROVAL,
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    # ========================================================================
    # UPDATE
    # ========================================================================

    def update(
        self,
        request,
        *args,
        **kwargs,
    ):

        if request.user.role == UserRole.DEALER:

            return Response(
                {
                    "error": (
                        "Dealers cannot modify "
                        "replacement kit requests."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().update(
            request,
            *args,
            **kwargs,
        )

    # ========================================================================
    # DELETE
    # ========================================================================

    def destroy(
        self,
        request,
        *args,
        **kwargs,
    ):

        if request.user.role not in [
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_ADMIN,
        ]:

            return Response(
                {
                    "success": False,
                    "error": (
                        "You do not have permission "
                        "to delete replacement kit requests."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = self.get_object()

        request_id = str(
            instance.id
        )

        try:

            instance.hard_delete()

            return Response(
                {
                    "success": True,
                    "message": (
                        "Replacement kit request "
                        "deleted successfully."
                    ),
                    "id": request_id,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Failed to delete "
                        "replacement kit request."
                    ),
                    "error": str(exc),
                    "id": request_id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    # ========================================================================
    # APPROVE
    # ========================================================================

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[
            IsAuthenticated,
            IsSuperAdmin,
        ],
    )
    def approve(
        self,
        request,
        pk=None,
    ):

        instance = self.get_object()

        instance.status = (
            InstallationStatus.APPROVED
        )

        admin_notes = request.data.get(
            "admin_notes",
            "",
        )

        if admin_notes:

            instance.admin_notes = admin_notes

        instance.save(
            update_fields=[
                "status",
                "admin_notes",
            ]
        )

        return Response(
            self.get_serializer(instance).data
        )

    # ========================================================================
    # DISAPPROVE
    # ========================================================================

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[
            IsAuthenticated,
            IsSuperAdmin,
        ],
    )
    def disapprove(
        self,
        request,
        pk=None,
    ):

        instance = self.get_object()

        instance.status = (
            InstallationStatus.DISAPPROVED
        )

        admin_notes = request.data.get(
            "admin_notes",
            "",
        )

        if admin_notes:

            instance.admin_notes = admin_notes

        instance.save(
            update_fields=[
                "status",
                "admin_notes",
            ]
        )

        return Response(
            self.get_serializer(instance).data
        )

    # ========================================================================
    # REJECT
    # ========================================================================

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[
            IsAuthenticated,
            IsSuperAdmin,
        ],
    )
    def reject(
        self,
        request,
        pk=None,
    ):

        instance = self.get_object()

        instance.status = (
            InstallationStatus.REJECTED
        )

        admin_notes = request.data.get(
            "admin_notes",
            "",
        )

        if admin_notes:

            instance.admin_notes = admin_notes

        instance.save(
            update_fields=[
                "status",
                "admin_notes",
            ]
        )

        return Response(
            self.get_serializer(instance).data
        )