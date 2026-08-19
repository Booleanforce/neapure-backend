from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from apps.notifications.models import Notification
from apps.notifications.api.serializers import NotificationSerializer

class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    API for users to fetch, read, and delete their notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_read", "notification_type", "event_type", "priority"]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user, is_deleted=False)

    def perform_destroy(self, instance):
        instance.soft_delete()

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"unread_count": count})

    @action(detail=True, methods=["patch"])
    def mark_as_read(self, request, pk=None):
        instance = self.get_object()
        if not instance.is_read:
            instance.is_read = True
            instance.read_at = timezone.now()
            instance.save(update_fields=["is_read", "read_at"])
        return Response(self.get_serializer(instance).data)

    @action(detail=False, methods=["patch"])
    def mark_all_as_read(self, request):
        now = timezone.now()
        self.get_queryset().filter(is_read=False).update(is_read=True, read_at=now)
        return Response({"status": "success", "message": "All notifications marked as read."})
