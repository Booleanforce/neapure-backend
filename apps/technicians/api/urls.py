from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.technicians.api.views import (
    AdminTechnicianViewSet, 
    OperationAdminJobViewSet, 
    OperationAdminTechnicianViewSet,
    TechnicianMyJobsViewSet,
    TechnicianMyProfileViewSet,
    TechnicianMyPerformanceViewSet
)

router = DefaultRouter()
router.register(r"admin/technicians", AdminTechnicianViewSet, basename="admin-technicians")
router.register(r"operations/jobs", OperationAdminJobViewSet, basename="operation-jobs")
router.register(r"operations/technicians", OperationAdminTechnicianViewSet, basename="operation-technicians")

router.register(r"dashboard/my-jobs", TechnicianMyJobsViewSet, basename="technician-my-jobs")
router.register(r"dashboard/my-profile", TechnicianMyProfileViewSet, basename="technician-my-profile")
router.register(r"dashboard/my-performance", TechnicianMyPerformanceViewSet, basename="technician-my-performance")

urlpatterns = [
    path("", include(router.urls)),
]
