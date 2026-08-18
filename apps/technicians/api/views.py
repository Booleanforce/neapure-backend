import uuid
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.accounts.models import User
from shared.constants.roles import UserRole
from apps.technicians.models import TechnicianProfile, TechnicianJob
from apps.technicians.api.serializers import TechnicianSerializer, TechnicianJobSerializer, TechnicianPerformanceSerializer
from apps.accounts.permissions import IsSuperAdmin, IsAdminUser, IsTechnician
from apps.accounts.services.account_service import AccountService

class AdminTechnicianViewSet(viewsets.ModelViewSet):
    """
    API for Super Admins to manage Technicians.
    """
    serializer_class = TechnicianSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["email", "full_name", "phone", "technician_profile__region"]
    ordering_fields = ["created_at", "email", "full_name"]
    ordering = ["-created_at"]
    filterset_fields = ["technician_profile__status", "is_active", "technician_profile__region"]

    def get_queryset(self):
        return User.objects.filter(role=UserRole.TECHNICIAN).select_related("technician_profile")

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["role"] = UserRole.TECHNICIAN
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data.copy()
        validated_data["password"] = request.data.get("password", "")
        validated_data["role"] = UserRole.TECHNICIAN
        
        if not validated_data.get("firebase_uid"):
            validated_data["firebase_uid"] = f"pending_{uuid.uuid4()}"
        
        # Pop nested profile data so User.objects.create_user doesn't fail
        validated_data.pop("technician_profile", None)
        
        user = AccountService.create_user(validated_data)

        # Profile fields
        profile_data = request.data.get("technician_profile", {})
        if profile_data:
            profile = user.technician_profile
            if "region" in profile_data:
                profile.region = profile_data["region"]
            if "skills" in profile_data:
                profile.skills = profile_data["skills"]
            if "status" in profile_data:
                profile.status = profile_data["status"]
            profile.save()

        return Response(TechnicianSerializer(user).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        profile = instance.technician_profile
        profile_data = request.data.get("technician_profile", {})
        if profile_data:
            if "region" in profile_data:
                profile.region = profile_data["region"]
            if "skills" in profile_data:
                profile.skills = profile_data["skills"]
            if "status" in profile_data:
                profile.status = profile_data["status"]
            profile.save()

        return Response(self.get_serializer(instance).data)

    def perform_destroy(self, instance):
        instance.delete()

class OperationAdminJobViewSet(viewsets.ModelViewSet):
    """
    API for Operations Admin to assign and manage jobs.
    """
    serializer_class = TechnicianJobSerializer
    permission_classes = [IsAuthenticated, IsAdminUser] # Allows SUPER_ADMIN and OPERATIONS_ADMIN
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["customer__email", "technician__email", "address", "notes"]
    ordering_fields = ["scheduled_date", "created_at", "priority"]
    ordering = ["-scheduled_date"]
    filterset_fields = ["status", "job_type", "priority", "technician"]

    def get_queryset(self):
        return TechnicianJob.objects.all().select_related("technician", "customer", "dealer", "product", "installation_request", "replacement_kit_request")

class OperationAdminTechnicianViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API for Operations Admin to view technicians and their performance.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = TechnicianPerformanceSerializer
    
    def get_queryset(self):
        from django.db.models import Count, Q, Avg
        return User.objects.filter(role=UserRole.TECHNICIAN).select_related("technician_profile").annotate(
            total_jobs=Count("assigned_jobs"),
            completed_jobs=Count("assigned_jobs", filter=Q(assigned_jobs__status="COMPLETED")),
            pending_jobs=Count("assigned_jobs", filter=Q(assigned_jobs__status__in=["ASSIGNED", "PENDING", "IN_PROGRESS"])),
            cancelled_jobs=Count("assigned_jobs", filter=Q(assigned_jobs__status="CANCELLED")),
            avg_rating=Avg("assigned_jobs__customer_rating")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        data = []
        for tech in queryset:
            data.append({
                "technician_id": tech.id,
                "full_name": tech.full_name,
                "email": tech.email,
                "status": tech.technician_profile.status if hasattr(tech, 'technician_profile') else "UNKNOWN",
                "total_jobs": tech.total_jobs,
                "completed_jobs": tech.completed_jobs,
                "pending_jobs": tech.pending_jobs,
                "cancelled_jobs": tech.cancelled_jobs,
                "average_rating": tech.avg_rating
            })
            
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)
        
    def retrieve(self, request, *args, **kwargs):
        tech = self.get_object()
        data = {
            "technician_id": tech.id,
            "full_name": tech.full_name,
            "email": tech.email,
            "status": tech.technician_profile.status if hasattr(tech, 'technician_profile') else "UNKNOWN",
            "total_jobs": tech.total_jobs,
            "completed_jobs": tech.completed_jobs,
            "pending_jobs": tech.pending_jobs,
            "cancelled_jobs": tech.cancelled_jobs,
            "average_rating": tech.avg_rating
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data)

class TechnicianMyJobsViewSet(viewsets.ModelViewSet):
    """
    API for Technicians to view and update their own jobs.
    """
    permission_classes = [IsAuthenticated, IsTechnician]
    serializer_class = TechnicianJobSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["customer__email", "address", "notes"]
    ordering_fields = ["scheduled_date", "priority"]
    ordering = ["-scheduled_date"]
    filterset_fields = ["status", "job_type"]

    def get_queryset(self):
        return TechnicianJob.objects.filter(technician=self.request.user).select_related("customer", "dealer", "product", "installation_request", "replacement_kit_request")

    def perform_create(self, serializer):
        # Technicians cannot create jobs
        pass

    def perform_destroy(self, instance):
        # Technicians cannot delete jobs
        pass

class TechnicianMyProfileViewSet(viewsets.GenericViewSet):
    """
    API for Technicians to view and update their own profile.
    """
    permission_classes = [IsAuthenticated, IsTechnician]
    serializer_class = TechnicianSerializer

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id).select_related("technician_profile")

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        user = self.get_queryset().first()
        if request.method == "GET":
            return Response(self.get_serializer(user).data)
        
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Only allow updating profile fields like skills, status
        profile_data = request.data.get("technician_profile", {})
        if profile_data:
            profile = user.technician_profile
            if "skills" in profile_data:
                profile.skills = profile_data["skills"]
            if "status" in profile_data:
                profile.status = profile_data["status"]
            profile.save()
            
        return Response(self.get_serializer(user).data)

class TechnicianMyPerformanceViewSet(viewsets.GenericViewSet):
    """
    API for Technicians to view their own performance.
    """
    permission_classes = [IsAuthenticated, IsTechnician]
    serializer_class = TechnicianPerformanceSerializer

    def get_queryset(self):
        from django.db.models import Count, Q, Avg
        return User.objects.filter(id=self.request.user.id).select_related("technician_profile").annotate(
            total_jobs=Count("assigned_jobs"),
            completed_jobs=Count("assigned_jobs", filter=Q(assigned_jobs__status="COMPLETED")),
            pending_jobs=Count("assigned_jobs", filter=Q(assigned_jobs__status__in=["ASSIGNED", "PENDING", "IN_PROGRESS"])),
            cancelled_jobs=Count("assigned_jobs", filter=Q(assigned_jobs__status="CANCELLED")),
            avg_rating=Avg("assigned_jobs__customer_rating")
        )

    @action(detail=False, methods=["get"])
    def me(self, request):
        tech = self.get_queryset().first()
        data = {
            "technician_id": tech.id,
            "full_name": tech.full_name,
            "email": tech.email,
            "status": tech.technician_profile.status if hasattr(tech, 'technician_profile') else "UNKNOWN",
            "total_jobs": tech.total_jobs,
            "completed_jobs": tech.completed_jobs,
            "pending_jobs": tech.pending_jobs,
            "cancelled_jobs": tech.cancelled_jobs,
            "average_rating": tech.avg_rating
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data)
