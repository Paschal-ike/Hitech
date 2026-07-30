from django.conf import settings
from django.contrib.gis.db import models

from core.models import TimeStampedModel, UUIDModel


class UploadSession(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS", "Completed with errors"

    survey = models.ForeignKey(
        "surveys.Survey",
        on_delete=models.CASCADE,
        related_name="upload_sessions",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="upload_sessions",
    )

    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.PROCESSING,
        db_index=True,
    )
    current_step = models.CharField(
        max_length=100,
        blank=True,
    )
    archive = models.FileField(
        upload_to="survey_uploads/",
    )
    progress = models.PositiveSmallIntegerField(
        default=0,
    )

    processing_started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    processing_completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    total_files = models.PositiveSmallIntegerField(default=0)
    processed_files = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "uploads_upload_session"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.survey.name} ({self.status})"


class SurveyFile(UUIDModel, TimeStampedModel):
    class FileFormat(models.TextChoices):
        ORTHOMOSAIC = "ORTHOMOSAIC", "Orthomosaic"
        DSM = "DSM", "Digital Surface Model"
        DTM = "DTM", "Digital Terrain Model"
        POINT_CLOUD = "POINT_CLOUD", "Point Cloud"
        MODEL = "MODEL", "3D Model"
        MESH = "MESH", "Mesh"
        KML = "KML", "KML"
        GEOJSON = "GEOJSON", "GeoJSON"
        METADATA = "METADATA", "Metadata"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        PENDING = "pending"
        COMPLETED = "completed"
        FAILED = "failed"

    survey = models.ForeignKey(
        "surveys.Survey",
        on_delete=models.CASCADE,
        related_name="files",
    )

    upload_session = models.ForeignKey(
        UploadSession,
        on_delete=models.CASCADE,
        related_name="files",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_files",
    )

    original_file = models.FileField(
        upload_to="surveys/original/",
    )

    converted_file = models.FileField(
        upload_to="surveys/converted/",
        null=True,
        blank=True,
    )

    preview_image = models.ImageField(
        upload_to="surveys/previews/",
        null=True,
        blank=True,
    )

    original_filename = models.CharField(
        max_length=255,
    )

    file_format = models.CharField(
        max_length=30,
        choices=FileFormat.choices,
    )

    relative_path = models.CharField(
        max_length=500,
    )

    mime_type = models.CharField(
        max_length=100,
    )

    file_size = models.BigIntegerField()

    checksum = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 checksum for duplicate detection.",
    )

    validation_passed = models.BooleanField(
        default=False,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    error_message = models.TextField(blank=True, default="")
    tile_directory = models.CharField(max_length=255, blank=True, default="")
    tile_bounds = models.JSONField(null=True, blank=True)
    model_path = models.CharField(max_length=255, blank=True, default="")
    point_cloud_directory = models.CharField(max_length=255, blank=True, default="")

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Extracted file metadata.",
    )

    class Meta:
        db_table = "uploads_survey_file"
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["survey"]),
            models.Index(fields=["upload_session"]),
            models.Index(fields=["checksum"]),
            models.Index(fields=["file_format"]),
        ]

    def __str__(self):
        return self.original_filename
