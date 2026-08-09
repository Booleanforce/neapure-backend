import json
import uuid

from django.db.models import Avg, Count, Q

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import (
    FormParser,
    JSONParser,
    MultiPartParser,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.accounts.models import User
from apps.accounts.permissions import (
    IsAdminUser,
    IsSuperAdmin,
    IsTechnician,
)
from apps.accounts.services.account_service import AccountService

from apps.technicians.models import (
    TechnicianJob,
    TechnicianProfile,
)

from apps.technicians.api.serializers import (
    TechnicianSerializer,
    TechnicianJobSerializer,
    TechnicianPerformanceSerializer,
)

from shared.constants.roles import UserRole


# ============================================================
# HELPERS
# ============================================================


def parse_profile_data(data):
    """
    Supports both JSON and multipart/form-data.

    JSON example:

    {
        "technician_profile": {
            "region": "Dhaka",
            "skills": "Repair",
            "status": "ACTIVE"
        }
    }

    FormData example:

    technician_profile =
    '{"region":"Dhaka","skills":"Repair","status":"ACTIVE"}'
    """

    profile_data = data.get(
        "technician_profile",
        {},
    )

    if not profile_data:
        return {}

    # Normal JSON request
    if isinstance(profile_data, dict):
        return profile_data

    # FormData request
    if isinstance(profile_data, str):
        try:
            parsed = json.loads(profile_data)

            if isinstance(parsed, dict):
                return parsed

        except json.JSONDecodeError:
            return {}

    return {}


def get_or_create_technician_profile(user):
    """
    Get the technician profile.

    If the profile does not exist, create it.
    """

    try:
        return user.technician_profile

    except TechnicianProfile.DoesNotExist:
        return TechnicianProfile.objects.create(
            user=user
        )


def update_technician_profile(
    user,
    request,
    allow_status=True,
):
    """
    Update technician profile information.

    Supports:

    - region
    - skills
    - status
    - profile_photo
    - remove_profile_photo
    """

    profile = get_or_create_technician_profile(
        user
    )

    profile_data = parse_profile_data(
        request.data
    )

    # --------------------------------------------------------
    # Region
    # --------------------------------------------------------

    if "region" in profile_data:
        profile.region = profile_data[
            "region"
        ]

    # --------------------------------------------------------
    # Skills
    # --------------------------------------------------------

    if "skills" in profile_data:
        profile.skills = profile_data[
            "skills"
        ]

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    if (
        allow_status
        and "status" in profile_data
    ):
        profile.status = profile_data[
            "status"
        ]

    # --------------------------------------------------------
    # Profile Photo Upload
    # --------------------------------------------------------

    profile_photo = request.FILES.get(
        "profile_photo"
    )

    if profile_photo:
        profile.profile_photo = profile_photo

    # --------------------------------------------------------
    # Remove Profile Photo
    # --------------------------------------------------------

    remove_photo = request.data.get(
        "remove_profile_photo"
    )

    if str(remove_photo).lower() in [
        "true",
        "1",
        "yes",
    ]:
        profile.profile_photo = None

    profile.save()

    return profile


# ============================================================
# ADMIN TECHNICIAN
# ============================================================


class AdminTechnicianViewSet(
    viewsets.ModelViewSet
):
    """
    Super Admin API for managing technicians.

    Supports:

    GET
    POST
    PUT
    PATCH
    DELETE

    Also supports profile photo upload.
    """

    serializer_class = TechnicianSerializer

    permission_classes = [
        IsAuthenticated,
        IsSuperAdmin,
    ]

    parser_classes = [
        JSONParser,
        MultiPartParser,
        FormParser,
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

    # ========================================================
    # QUERYSET
    # ========================================================

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

    # ========================================================
    # CREATE TECHNICIAN
    # ========================================================

    def create(
        self,
        request,
        *args,
        **kwargs,
    ):
        """
        Create a technician.

        Supports:
        - JSON
        - multipart/form-data
        - profile photo
        """

        # --------------------------------------------------------
        # Profile data
        # --------------------------------------------------------

        profile_data = parse_profile_data(
            request.data
        )

        profile_photo = request.FILES.get(
            "profile_photo"
        )

        # --------------------------------------------------------
        # User data
        # --------------------------------------------------------

        data = request.data.copy()

        # These belong to TechnicianProfile
        data.pop(
            "technician_profile",
            None,
        )

        data.pop(
            "profile_photo",
            None,
        )

        data.pop(
            "remove_profile_photo",
            None,
        )

        # --------------------------------------------------------
        # Force technician role
        # --------------------------------------------------------

        data["role"] = UserRole.TECHNICIAN

        # --------------------------------------------------------
        # Validate
        # --------------------------------------------------------

        serializer = self.get_serializer(
            data=data
        )

        serializer.is_valid(
            raise_exception=True
        )

        validated_data = (
            serializer.validated_data.copy()
        )

        # ========================================================
        # VERY IMPORTANT
        # ========================================================
        #
        # Your UserManager.create_user() does NOT accept:
        #
        # firebase_uid
        # is_active
        #
        # Therefore remove BOTH before AccountService.
        # ========================================================

        is_active = validated_data.pop(
            "is_active",
            True,
        )

        validated_data.pop(
            "firebase_uid",
            None,
        )

        # --------------------------------------------------------
        # Password
        # --------------------------------------------------------

        password = request.data.get(
            "password",
            ""
        )

        if not password:
            return Response(
                {
                    "password": [
                        "Password is required."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------------
        # Force role
        # --------------------------------------------------------

        validated_data["role"] = (
            UserRole.TECHNICIAN
        )

        # --------------------------------------------------------
        # Password
        # --------------------------------------------------------

        validated_data["password"] = password

        # ========================================================
        # DEBUG
        # ========================================================
        #
        # Temporarily keep this.
        # It lets you confirm firebase_uid is NOT being sent.
        # ========================================================

        print(
            "CREATE USER DATA:",
            validated_data
        )

        # ========================================================
        # CREATE USER
        # ========================================================

        user = AccountService.create_user(
            validated_data
        )

        # --------------------------------------------------------
        # is_active
        # --------------------------------------------------------

        user.is_active = is_active

        user.save(
            update_fields=[
                "is_active"
            ]
        )

        # --------------------------------------------------------
        # Firebase UID
        #
        # Set AFTER create_user().
        # --------------------------------------------------------

        if hasattr(
            user,
            "firebase_uid"
        ):
            if not user.firebase_uid:

                import uuid

                user.firebase_uid = (
                    f"pending_{uuid.uuid4()}"
                )

                user.save(
                    update_fields=[
                        "firebase_uid"
                    ]
                )

        # --------------------------------------------------------
        # Technician profile
        # --------------------------------------------------------

        profile = (
            get_or_create_technician_profile(
                user
            )
        )

        # --------------------------------------------------------
        # Region
        # --------------------------------------------------------

        if "region" in profile_data:
            profile.region = (
                profile_data["region"]
            )

        # --------------------------------------------------------
        # Skills
        # --------------------------------------------------------

        if "skills" in profile_data:
            profile.skills = (
                profile_data["skills"]
            )

        # --------------------------------------------------------
        # Status
        # --------------------------------------------------------

        if "status" in profile_data:
            profile.status = (
                profile_data["status"]
            )

        # --------------------------------------------------------
        # Profile photo
        # --------------------------------------------------------

        if profile_photo:
            profile.profile_photo = (
                profile_photo
            )

        profile.save()

        # --------------------------------------------------------
        # Refresh
        # --------------------------------------------------------

        user.refresh_from_db()

        # --------------------------------------------------------
        # Response
        # --------------------------------------------------------

        return Response(
            TechnicianSerializer(
                user
            ).data,
            status=status.HTTP_201_CREATED,
        )
    # ========================================================
    # UPDATE TECHNICIAN
    # ========================================================

    def update(
        self,
        request,
        *args,
        **kwargs,
    ):
        """
        Update technician.

        Supports:

        - User information
        - is_active
        - password
        - technician profile
        - profile photo
        """

        partial = kwargs.pop(
            "partial",
            False,
        )

        instance = self.get_object()

        # ----------------------------------------------------
        # Copy request data
        # ----------------------------------------------------

        user_data = request.data.copy()

        # ----------------------------------------------------
        # Remove profile-specific fields
        # ----------------------------------------------------

        user_data.pop(
            "technician_profile",
            None,
        )

        user_data.pop(
            "profile_photo",
            None,
        )

        user_data.pop(
            "remove_profile_photo",
            None,
        )

        # ----------------------------------------------------
        # Role cannot be changed
        # ----------------------------------------------------

        user_data.pop(
            "role",
            None,
        )

        # ----------------------------------------------------
        # Password handled separately
        # ----------------------------------------------------

        password = user_data.pop(
            "password",
            None,
        )

        # ----------------------------------------------------
        # Update User
        # ----------------------------------------------------

        serializer = self.get_serializer(
            instance,
            data=user_data,
            partial=partial,
        )

        serializer.is_valid(
            raise_exception=True
        )

        self.perform_update(
            serializer
        )

        # ----------------------------------------------------
        # Update Password
        # ----------------------------------------------------

        if password:
            instance.set_password(
                password
            )

            instance.save(
                update_fields=[
                    "password"
                ]
            )

        # ----------------------------------------------------
        # Update Technician Profile
        # ----------------------------------------------------

        update_technician_profile(
            user=instance,
            request=request,
            allow_status=True,
        )

        # ----------------------------------------------------
        # Refresh
        # ----------------------------------------------------

        instance.refresh_from_db()

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return Response(
            TechnicianSerializer(
                instance
            ).data
        )

    # ========================================================
    # DELETE TECHNICIAN
    # ========================================================

    def perform_destroy(
        self,
        instance,
    ):
        """
        Delete technician.
        """

        instance.delete()


# ============================================================
# OPERATIONS ADMIN - JOBS
# ============================================================


class OperationAdminJobViewSet(
    viewsets.ModelViewSet
):
    """
    Operations Admin API for assigning
    and managing technician jobs.
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


# ============================================================
# OPERATIONS ADMIN - TECHNICIANS
# ============================================================


class OperationAdminTechnicianViewSet(
    viewsets.ReadOnlyModelViewSet
):
    """
    Operations Admin API for viewing
    technicians and their performance.
    """

    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

    serializer_class = (
        TechnicianPerformanceSerializer
    )

    # ========================================================
    # QUERYSET
    # ========================================================

    def get_queryset(self):

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
                        assigned_jobs__status=(
                            "COMPLETED"
                        )
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
                        assigned_jobs__status=(
                            "CANCELLED"
                        )
                    ),
                ),

                avg_rating=Avg(
                    "assigned_jobs__customer_rating"
                ),
            )
        )

    # ========================================================
    # LIST
    # ========================================================

    def list(
        self,
        request,
        *args,
        **kwargs,
    ):

        queryset = self.get_queryset()

        data = []

        for tech in queryset:

            profile = getattr(
                tech,
                "technician_profile",
                None,
            )

            data.append(
                {
                    "technician_id": tech.id,

                    "full_name": (
                        tech.full_name
                    ),

                    "email": (
                        tech.email
                    ),

                    "status": (
                        profile.status
                        if profile
                        else "UNKNOWN"
                    ),

                    "total_jobs": (
                        tech.total_jobs
                    ),

                    "completed_jobs": (
                        tech.completed_jobs
                    ),

                    "pending_jobs": (
                        tech.pending_jobs
                    ),

                    "cancelled_jobs": (
                        tech.cancelled_jobs
                    ),

                    "average_rating": (
                        tech.avg_rating
                    ),
                }
            )

        serializer = self.get_serializer(
            data,
            many=True,
        )

        return Response(
            serializer.data
        )

    # ========================================================
    # RETRIEVE
    # ========================================================

    def retrieve(
        self,
        request,
        *args,
        **kwargs,
    ):

        tech = self.get_object()

        profile = getattr(
            tech,
            "technician_profile",
            None,
        )

        data = {
            "technician_id": tech.id,

            "full_name": (
                tech.full_name
            ),

            "email": (
                tech.email
            ),

            "status": (
                profile.status
                if profile
                else "UNKNOWN"
            ),

            "total_jobs": (
                tech.total_jobs
            ),

            "completed_jobs": (
                tech.completed_jobs
            ),

            "pending_jobs": (
                tech.pending_jobs
            ),

            "cancelled_jobs": (
                tech.cancelled_jobs
            ),

            "average_rating": (
                tech.avg_rating
            ),
        }

        serializer = self.get_serializer(
            data
        )

        return Response(
            serializer.data
        )


# ============================================================
# TECHNICIAN - MY JOBS
# ============================================================


class TechnicianMyJobsViewSet(
    viewsets.ModelViewSet
):
    """
    Technician API for viewing
    their assigned jobs.
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
                technician=self.request.user
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
        """
        Technicians cannot create jobs.
        """

        pass

    def perform_destroy(
        self,
        instance,
    ):
        """
        Technicians cannot delete jobs.
        """

        pass


# ============================================================
# TECHNICIAN - MY PROFILE
# ============================================================


class TechnicianMyProfileViewSet(
    viewsets.GenericViewSet
):
    """
    Technician API for viewing
    and updating their own profile.
    """

    permission_classes = [
        IsAuthenticated,
        IsTechnician,
    ]

    serializer_class = (
        TechnicianSerializer
    )

    parser_classes = [
        JSONParser,
        MultiPartParser,
        FormParser,
    ]

    # ========================================================
    # QUERYSET
    # ========================================================

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

    # ========================================================
    # ME
    # ========================================================

    @action(
        detail=False,
        methods=[
            "get",
            "patch",
        ],
    )
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
                    "detail": (
                        "Technician profile "
                        "not found."
                    )
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        # ----------------------------------------------------
        # GET
        # ----------------------------------------------------

        if request.method == "GET":

            return Response(
                self.get_serializer(
                    user
                ).data
            )

        # ----------------------------------------------------
        # PATCH
        # ----------------------------------------------------

        user_data = request.data.copy()

        # Remove technician profile data
        user_data.pop(
            "technician_profile",
            None,
        )

        # Remove photo
        user_data.pop(
            "profile_photo",
            None,
        )

        # Remove photo flag
        user_data.pop(
            "remove_profile_photo",
            None,
        )

        # Technician cannot change role
        user_data.pop(
            "role",
            None,
        )

        # Technician cannot modify is_active
        user_data.pop(
            "is_active",
            None,
        )

        # ----------------------------------------------------
        # Update User
        # ----------------------------------------------------

        serializer = self.get_serializer(
            user,
            data=user_data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        self.perform_update(
            serializer
        )

        # ----------------------------------------------------
        # Update profile
        #
        # Status disabled for technician.
        # ----------------------------------------------------

        update_technician_profile(
            user=user,
            request=request,
            allow_status=False,
        )

        user.refresh_from_db()

        return Response(
            self.get_serializer(
                user
            ).data
        )


# ============================================================
# TECHNICIAN - MY PERFORMANCE
# ============================================================


class TechnicianMyPerformanceViewSet(
    viewsets.GenericViewSet
):
    """
    Technician API for viewing
    their own performance.
    """

    permission_classes = [
        IsAuthenticated,
        IsTechnician,
    ]

    serializer_class = (
        TechnicianPerformanceSerializer
    )

    # ========================================================
    # QUERYSET
    # ========================================================

    def get_queryset(self):

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
                        assigned_jobs__status=(
                            "COMPLETED"
                        )
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
                        assigned_jobs__status=(
                            "CANCELLED"
                        )
                    ),
                ),

                avg_rating=Avg(
                    "assigned_jobs__customer_rating"
                ),
            )
        )

    # ========================================================
    # ME
    # ========================================================

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
                    "detail": (
                        "Technician not found."
                    )
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        profile = getattr(
            tech,
            "technician_profile",
            None,
        )

        data = {
            "technician_id": tech.id,

            "full_name": (
                tech.full_name
            ),

            "email": (
                tech.email
            ),

            "status": (
                profile.status
                if profile
                else "UNKNOWN"
            ),

            "total_jobs": (
                tech.total_jobs
            ),

            "completed_jobs": (
                tech.completed_jobs
            ),

            "pending_jobs": (
                tech.pending_jobs
            ),

            "cancelled_jobs": (
                tech.cancelled_jobs
            ),

            "average_rating": (
                tech.avg_rating
            ),
        }

        serializer = self.get_serializer(
            data
        )

        return Response(
            serializer.data
        )