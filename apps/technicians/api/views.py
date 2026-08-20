import json
import uuid

from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.accounts.models import User
from shared.constants.roles import UserRole

from apps.technicians.models import (
    TechnicianProfile,
    TechnicianJob,
)

from apps.technicians.api.serializers import (
    TechnicianSerializer,
    TechnicianJobSerializer,
    TechnicianPerformanceSerializer,
)

from apps.accounts.permissions import (
    IsSuperAdmin,
    IsAdminUser,
    IsTechnician,
)

from apps.accounts.services.account_service import (
    AccountService,
)


# ============================================================================
# HELPERS
# ============================================================================

def normalize_string(value):
    """
    Safely convert API values to strings.
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, (int, float, bool)):
        return str(value)

    if isinstance(value, list):
        return ", ".join(
            normalize_string(item)
            for item in value
            if item is not None
        ).strip()

    if isinstance(value, dict):
        return json.dumps(
            value,
            ensure_ascii=False,
        )

    return str(value).strip()


def normalize_skills(value):
    """
    Skills can arrive as:

    - string
    - list
    - dict
    - None
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):
        return ", ".join(
            normalize_string(item)
            for item in value
            if item is not None
        ).strip()

    if isinstance(value, dict):
        return json.dumps(
            value,
            ensure_ascii=False,
        )

    return str(value).strip()


def parse_profile_data(data):
    """
    Supports:

    1. JSON object

       {
           "technician_profile": {
               "region": "Dhaka",
               "skills": "Installation",
               "status": "ACTIVE"
           }
       }

    2. JSON string

       technician_profile='{
           "region":"Dhaka",
           "skills":"Installation",
           "status":"ACTIVE"
       }'

    3. Flat multipart fields

       region=Dhaka
       skills=Installation
       status=ACTIVE

    Flat fields override nested values.
    """

    profile_data = {}

    # ------------------------------------------------------------------------
    # Nested technician_profile
    # ------------------------------------------------------------------------

    nested = data.get(
        "technician_profile"
    )

    if isinstance(
        nested,
        dict,
    ):
        profile_data = nested.copy()

    elif isinstance(
        nested,
        str,
    ):
        try:
            parsed = json.loads(
                nested
            )

            if isinstance(
                parsed,
                dict,
            ):
                profile_data = parsed

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            profile_data = {}

    # ------------------------------------------------------------------------
    # Flat values override nested values
    # ------------------------------------------------------------------------

    for field in (
        "region",
        "skills",
        "status",
    ):
        if field in data:
            profile_data[field] = data.get(
                field
            )

    # ------------------------------------------------------------------------
    # Normalize
    # ------------------------------------------------------------------------

    if "region" in profile_data:
        profile_data["region"] = normalize_string(
            profile_data["region"]
        )

    if "skills" in profile_data:
        profile_data["skills"] = normalize_skills(
            profile_data["skills"]
        )

    if "status" in profile_data:
        profile_data["status"] = (
            normalize_string(
                profile_data["status"]
            ).upper()
        )

    return profile_data


def get_profile_photo_file(request):
    """
    Supports both frontend field names.
    """

    return (
        request.FILES.get(
            "profile_photo"
        )
        or request.FILES.get(
            "photo"
        )
    )


def get_remove_photo_flag(request):
    value = request.data.get(
        "remove_profile_photo",
        ""
    )

    return str(
        value
    ).lower() == "true"


def serialize_technician(user):
    """
    Always return a fresh serializer response.
    """

    user.refresh_from_db()

    return TechnicianSerializer(
        user
    ).data


# ============================================================================
# ADMIN TECHNICIAN VIEWSET
# ============================================================================

class AdminTechnicianViewSet(
    viewsets.ModelViewSet
):
    """
    Super Admin API for managing technicians.
    """

    serializer_class = TechnicianSerializer

    permission_classes = [
        IsAuthenticated,
        IsSuperAdmin,
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = [
        "email",
        "full_name",
        "phone",
        "technician_profile__region",
    ]

    ordering_fields = [
        "created_at",
        "email",
        "full_name",
    ]

    ordering = [
        "-created_at"
    ]

    filterset_fields = [
        "technician_profile__status",
        "is_active",
        "technician_profile__region",
    ]

    # ========================================================================
    # QUERYSET
    # ========================================================================

    def get_queryset(self):
        return (
            User.objects
            .filter(
                role=UserRole.TECHNICIAN
            )
            .select_related(
                "technician_profile"
            )
        )

    # ========================================================================
    # CREATE
    # ========================================================================

    @transaction.atomic
    def create(
        self,
        request,
        *args,
        **kwargs,
    ):
        try:
            print(
                "========================================"
            )
            print(
                "===== CREATE TECHNICIAN ====="
            )
            print(
                "Content-Type:",
                request.content_type,
            )
            print(
                "Request data:",
                request.data,
            )
            print(
                "Request files:",
                request.FILES,
            )
            print(
                "========================================"
            )

            # ----------------------------------------------------------------
            # BASIC USER DATA
            # ----------------------------------------------------------------

            email = normalize_string(
                request.data.get(
                    "email"
                )
            )

            full_name = normalize_string(
                request.data.get(
                    "full_name"
                )
            )

            phone = normalize_string(
                request.data.get(
                    "phone"
                )
            )

            password = (
                request.data.get(
                    "password"
                )
                or ""
            )

            if not email:
                return Response(
                    {
                        "detail":
                            "Email is required."
                    },
                    status=
                    status.HTTP_400_BAD_REQUEST,
                )

            if not full_name:
                return Response(
                    {
                        "detail":
                            "Full name is required."
                    },
                    status=
                    status.HTTP_400_BAD_REQUEST,
                )

            if not password:
                return Response(
                    {
                        "detail":
                            "Password is required."
                    },
                    status=
                    status.HTTP_400_BAD_REQUEST,
                )

            # ----------------------------------------------------------------
            # DUPLICATE EMAIL
            # ----------------------------------------------------------------

            if User.objects.filter(
                email__iexact=email
            ).exists():
                return Response(
                    {
                        "detail":
                            "A user with this email already exists."
                    },
                    status=
                    status.HTTP_400_BAD_REQUEST,
                )

            # ----------------------------------------------------------------
            # PROFILE
            # ----------------------------------------------------------------

            profile_data = parse_profile_data(
                request.data
            )

            region = normalize_string(
                profile_data.get(
                    "region"
                )
            )

            skills = normalize_skills(
                profile_data.get(
                    "skills"
                )
            )

            profile_status = (
                normalize_string(
                    profile_data.get(
                        "status"
                    )
                    or "ACTIVE"
                ).upper()
            )

            if profile_status not in {
                "ACTIVE",
                "BLOCKED",
            }:
                profile_status = "ACTIVE"

            # ----------------------------------------------------------------
            # CREATE USER
            # ----------------------------------------------------------------

            user_data = {
                "email": email,
                "full_name": full_name,
                "phone": phone,
                "password": password,
                "role": UserRole.TECHNICIAN,
                "firebase_uid":
                    f"pending_{uuid.uuid4()}",
                "is_active": True,
            }

            print(
                "User data:",
                {
                    key: (
                        "***"
                        if key == "password"
                        else value
                    )
                    for key, value
                    in user_data.items()
                }
            )

            user = (
                AccountService.create_user(
                    user_data
                )
            )

            # Make absolutely sure a technician can log in.
            if not user.is_active:
                user.is_active = True

                user.save(
                    update_fields=[
                        "is_active"
                    ]
                )

            # Make sure the role is correct.
            if (
                user.role
                != UserRole.TECHNICIAN
            ):
                user.role = (
                    UserRole.TECHNICIAN
                )

                user.save(
                    update_fields=[
                        "role"
                    ]
                )

            # ----------------------------------------------------------------
            # PROFILE
            # ----------------------------------------------------------------

            profile, _ = (
                TechnicianProfile.objects.get_or_create(
                    user=user
                )
            )

            profile.region = region
            profile.skills = skills
            profile.status = profile_status

            # ----------------------------------------------------------------
            # PHOTO
            # ----------------------------------------------------------------

            photo_file = (
                get_profile_photo_file(
                    request
                )
            )

            if photo_file:
                profile.profile_photo = (
                    photo_file
                )

            profile.save()

            # ----------------------------------------------------------------
            # RESPONSE
            # ----------------------------------------------------------------

            print(
                "Technician created:",
                user.id,
                user.email,
                "is_active:",
                user.is_active,
            )

            return Response(
                serialize_technician(
                    user
                ),
                status=
                status.HTTP_201_CREATED,
            )

        except Exception as exc:
            import traceback

            print(
                "========================================"
            )
            print(
                "TECHNICIAN CREATE ERROR"
            )
            print(
                str(exc)
            )
            traceback.print_exc()
            print(
                "========================================"
            )

            return Response(
                {
                    "detail":
                        str(exc),
                    "error":
                        "Technician creation failed.",
                },
                status=
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # ========================================================================
    # UPDATE
    # ========================================================================

    @transaction.atomic
    def update(
        self,
        request,
        *args,
        **kwargs,
    ):
        partial = kwargs.pop(
            "partial",
            False,
        )

        instance = self.get_object()

        print(
            "========================================"
        )
        print(
            "===== UPDATE TECHNICIAN ====="
        )
        print(
            "Technician:",
            instance.id,
        )
        print(
            "Request data:",
            request.data,
        )
        print(
            "Request files:",
            request.FILES,
        )
        print(
            "========================================"
        )

        # ----------------------------------------------------------------
        # Parse profile data
        # ----------------------------------------------------------------

        profile_data = parse_profile_data(
            request.data
        )

        # ----------------------------------------------------------------
        # USER SERIALIZER DATA
        #
        # technician_profile MUST NOT be passed
        # into TechnicianSerializer here because
        # we update TechnicianProfile manually.
        # ----------------------------------------------------------------

        serializer_data = (
            request.data.copy()
        )

        serializer_data.pop(
            "technician_profile",
            None,
        )

        # Protected fields.
        serializer_data.pop(
            "role",
            None,
        )

        serializer_data.pop(
            "firebase_uid",
            None,
        )

        # ----------------------------------------------------------------
        # USER UPDATE
        # ----------------------------------------------------------------

        serializer = (
            self.get_serializer(
                instance,
                data=serializer_data,
                partial=partial,
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        # ----------------------------------------------------------------
        # PROFILE
        # ----------------------------------------------------------------

        profile, _ = (
            TechnicianProfile.objects.get_or_create(
                user=instance
            )
        )

        # ----------------------------------------------------------------
        # REGION
        # ----------------------------------------------------------------

        if "region" in profile_data:
            profile.region = (
                normalize_string(
                    profile_data.get(
                        "region"
                    )
                )
            )

        # ----------------------------------------------------------------
        # SKILLS
        # ----------------------------------------------------------------

        if "skills" in profile_data:
            profile.skills = (
                normalize_skills(
                    profile_data.get(
                        "skills"
                    )
                )
            )

        # ----------------------------------------------------------------
        # STATUS
        # ----------------------------------------------------------------

        if "status" in profile_data:
            new_status = (
                normalize_string(
                    profile_data.get(
                        "status"
                    )
                ).upper()
            )

            if new_status in {
                "ACTIVE",
                "BLOCKED",
            }:
                profile.status = (
                    new_status
                )

        # ----------------------------------------------------------------
        # PHOTO
        # ----------------------------------------------------------------

        photo_file = (
            get_profile_photo_file(
                request
            )
        )

        if photo_file:
            profile.profile_photo = (
                photo_file
            )

        # ----------------------------------------------------------------
        # REMOVE PHOTO
        # ----------------------------------------------------------------

        if (
            get_remove_photo_flag(
                request
            )
            and not photo_file
        ):
            if profile.profile_photo:
                profile.profile_photo.delete(
                    save=False
                )

            profile.profile_photo = None

        profile.save()

        return Response(
            serialize_technician(
                instance
            ),
            status=
            status.HTTP_200_OK,
        )

    # ========================================================================
    # DELETE
    # ========================================================================

    @transaction.atomic
    def destroy(
        self,
        request,
        *args,
        **kwargs,
    ):
        """
        Permanently delete a technician.

        QuerySet.delete() is intentionally used
        instead of instance.delete().
        """

        technician_id = kwargs.get(
            self.lookup_field,
            kwargs.get(
                "pk"
            ),
        )

        technician = get_object_or_404(
            self.get_queryset(),
            pk=technician_id,
        )

        deleted_id = str(
            technician.id
        )

        deleted_email = (
            technician.email
        )

        deleted_name = (
            technician.full_name
        )

        print(
            "========================================"
        )
        print(
            "[DELETE TECHNICIAN]"
        )
        print(
            {
                "id":
                    deleted_id,
                "email":
                    deleted_email,
                "name":
                    deleted_name,
            }
        )
        print(
            "========================================"
        )

        # ----------------------------------------------------------------
        # IMPORTANT
        # ----------------------------------------------------------------
        # QuerySet.delete() returns:
        #
        # (deleted_count, deleted_details)
        # ----------------------------------------------------------------

        (
            deleted_count,
            deleted_details,
        ) = (
            User.objects
            .filter(
                pk=technician.id,
                role=UserRole.TECHNICIAN,
            )
            .delete()
        )

        print(
            "[DELETE TECHNICIAN RESULT]",
            {
                "deleted_count":
                    deleted_count,
                "deleted_details":
                    deleted_details,
            },
        )

        # ----------------------------------------------------------------
        # VERIFY
        # ----------------------------------------------------------------

        still_exists = (
            User.objects
            .filter(
                pk=technician.id
            )
            .exists()
        )

        print(
            "[DELETE TECHNICIAN VERIFY]",
            {
                "id":
                    deleted_id,
                "still_exists":
                    still_exists,
            },
        )

        if still_exists:
            return Response(
                {
                    "success": False,
                    "message":
                        "Technician could not be deleted.",
                    "deleted_id":
                        deleted_id,
                },
                status=
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "success": True,
                "message":
                    "Technician deleted successfully.",
                "deleted_id":
                    deleted_id,
                "email":
                    deleted_email,
                "name":
                    deleted_name,
            },
            status=
            status.HTTP_200_OK,
        )


# ============================================================================
# OPERATION ADMIN JOB
# ============================================================================

class OperationAdminJobViewSet(
    viewsets.ModelViewSet
):
    """
    Operations Admin API for managing technician jobs.
    """

    serializer_class = (
        TechnicianJobSerializer
    )

    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = [
        "customer__email",
        "technician__email",
        "address",
        "notes",
    ]

    ordering_fields = [
        "scheduled_date",
        "created_at",
        "priority",
    ]

    ordering = [
        "-scheduled_date"
    ]

    filterset_fields = [
        "status",
        "job_type",
        "priority",
        "technician",
    ]

    def get_queryset(self):
        return (
            TechnicianJob.objects
            .all()
            .select_related(
                "technician",
                "customer",
                "dealer",
                "product",
                "installation_request",
                "replacement_kit_request",
            )
        )


# ============================================================================
# OPERATION ADMIN TECHNICIAN
# ============================================================================

class OperationAdminTechnicianViewSet(
    viewsets.ReadOnlyModelViewSet
):
    """
    Operations Admin API for technician performance.
    """

    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

    serializer_class = (
        TechnicianPerformanceSerializer
    )

    def get_queryset(self):
        from django.db.models import (
            Count,
            Q,
            Avg,
        )

        return (
            User.objects
            .filter(
                role=UserRole.TECHNICIAN
            )
            .select_related(
                "technician_profile"
            )
            .annotate(
                total_jobs=Count(
                    "assigned_jobs"
                ),

                completed_jobs=Count(
                    "assigned_jobs",
                    filter=Q(
                        assigned_jobs__status=
                        "COMPLETED"
                    ),
                ),

                pending_jobs=Count(
                    "assigned_jobs",
                    filter=Q(
                        assigned_jobs__status__in=[
                            "ASSIGNED",
                            "PENDING",
                            "IN_PROGRESS",
                        ]
                    ),
                ),

                cancelled_jobs=Count(
                    "assigned_jobs",
                    filter=Q(
                        assigned_jobs__status=
                        "CANCELLED"
                    ),
                ),

                avg_rating=Avg(
                    "assigned_jobs__customer_rating"
                ),
            )
        )

    def _build_performance_data(
        self,
        tech,
    ):
        return {
            "technician_id":
                tech.id,

            "full_name":
                tech.full_name,

            "email":
                tech.email,

            "status": (
                tech
                .technician_profile
                .status
                if hasattr(
                    tech,
                    "technician_profile",
                )
                else "UNKNOWN"
            ),

            "total_jobs":
                tech.total_jobs,

            "completed_jobs":
                tech.completed_jobs,

            "pending_jobs":
                tech.pending_jobs,

            "cancelled_jobs":
                tech.cancelled_jobs,

            "average_rating":
                tech.avg_rating,
        }

    def list(
        self,
        request,
        *args,
        **kwargs,
    ):
        queryset = (
            self.get_queryset()
        )

        data = [
            self._build_performance_data(
                tech
            )
            for tech in queryset
        ]

        serializer = (
            self.get_serializer(
                data,
                many=True,
            )
        )

        return Response(
            serializer.data
        )

    def retrieve(
        self,
        request,
        *args,
        **kwargs,
    ):
        tech = (
            self.get_object()
        )

        data = (
            self._build_performance_data(
                tech
            )
        )

        serializer = (
            self.get_serializer(
                data
            )
        )

        return Response(
            serializer.data
        )


# ============================================================================
# TECHNICIAN MY JOBS
# ============================================================================

class TechnicianMyJobsViewSet(
    viewsets.ModelViewSet
):
    """
    Technician can view/update own jobs.

    Technicians cannot create jobs
    and cannot delete jobs.
    """

    permission_classes = [
        IsAuthenticated,
        IsTechnician,
    ]

    serializer_class = (
        TechnicianJobSerializer
    )

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = [
        "customer__email",
        "address",
        "notes",
    ]

    ordering_fields = [
        "scheduled_date",
        "priority",
    ]

    ordering = [
        "-scheduled_date"
    ]

    filterset_fields = [
        "status",
        "job_type",
    ]

    def get_queryset(self):
        return (
            TechnicianJob.objects
            .filter(
                technician=
                self.request.user
            )
            .select_related(
                "customer",
                "dealer",
                "product",
                "installation_request",
                "replacement_kit_request",
            )
        )

    def perform_create(
        self,
        serializer,
    ):
        from rest_framework.exceptions import (
            MethodNotAllowed,
        )

        raise MethodNotAllowed(
            "POST"
        )

    def perform_destroy(
        self,
        instance,
    ):
        from rest_framework.exceptions import (
            MethodNotAllowed,
        )

        raise MethodNotAllowed(
            "DELETE"
        )


# ============================================================================
# TECHNICIAN MY PROFILE
# ============================================================================

class TechnicianMyProfileViewSet(
    viewsets.GenericViewSet
):
    """
    Technician can view and update
    their own profile.
    """

    permission_classes = [
        IsAuthenticated,
        IsTechnician,
    ]

    serializer_class = (
        TechnicianSerializer
    )

    def get_queryset(self):
        return (
            User.objects
            .filter(
                id=self.request.user.id
            )
            .select_related(
                "technician_profile"
            )
        )

    @action(
        detail=False,
        methods=[
            "get",
            "patch",
        ],
    )
    @transaction.atomic
    def me(
        self,
        request,
    ):
        user = (
            self.get_queryset()
            .first()
        )

        if not user:
            return Response(
                {
                    "detail":
                        "Technician profile not found."
                },
                status=
                status.HTTP_404_NOT_FOUND,
            )

        # ====================================================================
        # GET
        # ====================================================================

        if request.method == "GET":
            return Response(
                serialize_technician(
                    user
                ),
                status=
                status.HTTP_200_OK,
            )

        # ====================================================================
        # PARSE REQUEST
        # ====================================================================

        profile_data = parse_profile_data(
            request.data
        )

        # ====================================================================
        # LANGUAGE
        # ====================================================================

        requested_language = (
            request.data.get(
                "language"
            )
        )

        if requested_language is not None:
            requested_language = (
                normalize_string(
                    requested_language
                ).lower()
            )

            if requested_language not in {
                "en",
                "bn",
            }:
                return Response(
                    {
                        "detail":
                            "Language must be either 'en' or 'bn'."
                    },
                    status=
                    status.HTTP_400_BAD_REQUEST,
                )

        # ====================================================================
        # USER DATA
        #
        # Do NOT pass technician_profile
        # to TechnicianSerializer.
        # ====================================================================

        serializer_data = (
            request.data.copy()
        )

        serializer_data.pop(
            "technician_profile",
            None,
        )

        # Technicians cannot change role.
        serializer_data.pop(
            "role",
            None,
        )

        # Technicians cannot activate/deactivate
        # their account themselves.
        serializer_data.pop(
            "is_active",
            None,
        )

        # Technicians cannot change Firebase UID.
        serializer_data.pop(
            "firebase_uid",
            None,
        )

        # ====================================================================
        # USER VALIDATION
        # ====================================================================

        serializer = (
            self.get_serializer(
                user,
                data=serializer_data,
                partial=True,
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        # ====================================================================
        # PROFILE
        # ====================================================================

        profile, _ = (
            TechnicianProfile.objects.get_or_create(
                user=user
            )
        )

        # ====================================================================
        # REGION
        # ====================================================================

        if "region" in profile_data:
            profile.region = normalize_string(
                profile_data.get(
                    "region"
                )
            )

        # ====================================================================
        # SKILLS
        # ====================================================================

        if "skills" in profile_data:
            profile.skills = normalize_skills(
                profile_data.get(
                    "skills"
                )
            )

        # ====================================================================
        # STATUS
        #
        # IMPORTANT:
        # A technician should NOT be able to
        # block/activate their own account.
        #
        # Only update status when it is sent by
        # another trusted backend flow.
        # ====================================================================

        # Intentionally ignored here.

        # ====================================================================
        # PROFILE PHOTO
        # ====================================================================

        photo_file = (
            get_profile_photo_file(
                request
            )
        )

        if photo_file:
            profile.profile_photo = (
                photo_file
            )

        # ====================================================================
        # REMOVE PROFILE PHOTO
        # ====================================================================

        if (
            get_remove_photo_flag(
                request
            )
            and not photo_file
        ):
            if profile.profile_photo:
                profile.profile_photo.delete(
                    save=False
                )

            profile.profile_photo = None

        profile.save()

        # ====================================================================
        # LANGUAGE
        # ====================================================================

        if requested_language is not None:
            user.language = (
                requested_language
            )

            user.save(
                update_fields=[
                    "language"
                ]
            )

        # ====================================================================
        # RESPONSE
        # ====================================================================

        return Response(
            serialize_technician(
                user
            ),
            status=
            status.HTTP_200_OK,
        )


# ============================================================================
# TECHNICIAN MY PERFORMANCE
# ============================================================================

class TechnicianMyPerformanceViewSet(
    viewsets.GenericViewSet
):
    """
    Technician performance API.
    """

    permission_classes = [
        IsAuthenticated,
        IsTechnician,
    ]

    serializer_class = (
        TechnicianPerformanceSerializer
    )

    def get_queryset(self):
        from django.db.models import (
            Count,
            Q,
            Avg,
        )

        return (
            User.objects
            .filter(
                id=self.request.user.id
            )
            .select_related(
                "technician_profile"
            )
            .annotate(
                total_jobs=Count(
                    "assigned_jobs"
                ),

                completed_jobs=Count(
                    "assigned_jobs",
                    filter=Q(
                        assigned_jobs__status=
                        "COMPLETED"
                    ),
                ),

                pending_jobs=Count(
                    "assigned_jobs",
                    filter=Q(
                        assigned_jobs__status__in=[
                            "ASSIGNED",
                            "PENDING",
                            "IN_PROGRESS",
                        ]
                    ),
                ),

                cancelled_jobs=Count(
                    "assigned_jobs",
                    filter=Q(
                        assigned_jobs__status=
                        "CANCELLED"
                    ),
                ),

                avg_rating=Avg(
                    "assigned_jobs__customer_rating"
                ),
            )
        )

    @action(
        detail=False,
        methods=["get"],
    )
    def me(
        self,
        request,
    ):
        tech = (
            self.get_queryset()
            .first()
        )

        if not tech:
            return Response(
                {
                    "detail":
                        "Technician not found."
                },
                status=
                status.HTTP_404_NOT_FOUND,
            )

        data = {
            "technician_id":
                tech.id,

            "full_name":
                tech.full_name,

            "email":
                tech.email,

            "status": (
                tech
                .technician_profile
                .status
                if hasattr(
                    tech,
                    "technician_profile",
                )
                else "UNKNOWN"
            ),

            "total_jobs":
                tech.total_jobs,

            "completed_jobs":
                tech.completed_jobs,

            "pending_jobs":
                tech.pending_jobs,

            "cancelled_jobs":
                tech.cancelled_jobs,

            "average_rating":
                tech.avg_rating,
        }

        serializer = (
            self.get_serializer(
                data
            )
        )

        return Response(
            serializer.data,
            status=
            status.HTTP_200_OK,
        )