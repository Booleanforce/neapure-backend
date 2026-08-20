from django.db import models
from django.utils import timezone


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        """
        Soft delete.

        This does NOT remove the database record.
        It only marks the record as deleted.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()

        self.save(
            update_fields=[
                "is_deleted",
                "deleted_at",
            ]
        )

    def soft_delete(self):
        """
        Explicit soft delete.
        """
        self.delete()

    def hard_delete(self, *args, **kwargs):
        """
        Permanently delete this object from the database.

        This bypasses SoftDeleteModel.delete()
        and calls Django's actual Model.delete().
        """
        return super().delete(*args, **kwargs)