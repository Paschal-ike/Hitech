from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models

from core.models import TimeStampedModel, UUIDModel


class AuditLog(UUIDModel, TimeStampedModel):
    class Action(models.TextChoices):
        SURVEY_CREATED = "SURVEY_CREATED", "Survey Created"
        FILE_UPLOADED = "FILE_UPLOADED", "File Uploaded"
        FILE_UPLOAD_FAILED = "FILE_UPLOAD_FAILED", "File Upload Failed"
        PROCESSING_STARTED = "PROCESSING_STARTED", "Processing Started"
        PROCESSING_FAILED = "PROCESSING_FAILED", "Processing Failed"
        PROCESSING_RETRIED = "PROCESSING_RETRIED", "Processing Retried"
        SURVEY_APPROVED = "SURVEY_APPROVED", "Survey Approved"
        SURVEY_REJECTED = "SURVEY_REJECTED", "Survey Rejected"
        SURVEY_ARCHIVED = "SURVEY_ARCHIVED", "Survey Archived"
        FILE_DOWNLOADED = "FILE_DOWNLOADED", "File Downloaded"
        MEASUREMENT_CREATED = "MEASUREMENT_CREATED", "Measurement Created"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="audit_logs",
    )

    action = models.CharField(
        max_length=50,
        choices=Action.choices,
        db_index=True,
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
    )

    object_id = models.UUIDField()

    content_object = GenericForeignKey(
        "content_type",
        "object_id",
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "audit_audit_log"

        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.action}"
