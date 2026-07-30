from django.conf import settings
from django.contrib.gis.db import models

from core.models import CreatedByModel, TimeStampedModel, UUIDModel
from projects.models import Project, Site
from uploads.models import SurveyFile

class Survey(UUIDModel, TimeStampedModel, CreatedByModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        UPLOADING = "UPLOADING", "Uploading"
        READY = "READY", "Ready"
        APPROVED = "APPROVED", "Approved"
        ARCHIVED = "ARCHIVED", "Archived"

    class ProcessingStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="surveys",
    )

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="surveys",
    )

    name = models.CharField(
        max_length=255,
        help_text="Human-readable survey name.",
    )

    description = models.TextField(
        blank=True,
    )

    survey_date = models.DateField(
        db_index=True,
    )

    drone_model = models.CharField(
        max_length=255,
    )

    pilot = models.CharField(
        max_length=255,
        help_text="Name of the drone pilot.",
    )

    coordinate_reference_system = models.CharField(
        max_length=50,
        help_text="Coordinate Reference System (e.g. EPSG:4326).",
    )

    boundary = models.PolygonField(
        geography=True,
        null=True,
        blank=True,
        help_text="Survey coverage boundary.",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        db_index=True,
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_surveys",
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    rejection_reason = models.TextField(
        blank=True,
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )
    model_directory = models.CharField(
        max_length=500,
        blank=True,
    )

    tile_directory = models.CharField(
        max_length=500,
        blank=True,
    )

    class Meta:
        db_table = "surveys_survey"
        ordering = ["-survey_date", "-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["site", "survey_date"],
                name="unique_site_survey_date",
            )
        ]

        indexes = [
            models.Index(fields=["project"]),
            models.Index(fields=["site"]),
            models.Index(fields=["status"]),
            models.Index(fields=["processing_status"]),
            models.Index(fields=["survey_date"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.survey_date})"

    @property
    def has_2d_viewer(self):
        return self.files.filter(
            status=SurveyFile.Status.COMPLETED,
            file_format=SurveyFile.FileFormat.ORTHOMOSAIC,
        ).exists()

    @property
    def has_3d_viewer(self):
        return self.files.filter(
            status=SurveyFile.Status.COMPLETED,
            file_format__in=[
                SurveyFile.FileFormat.MODEL,
                SurveyFile.FileFormat.MESH,
                SurveyFile.FileFormat.POINT_CLOUD,
            ],
        ).exists()


class Measurement(UUIDModel, TimeStampedModel, CreatedByModel):
    class Type(models.TextChoices):
        DISTANCE = "DISTANCE", "Distance"
        AREA = "AREA", "Area"

    survey = models.ForeignKey(
        "Survey",
        on_delete=models.CASCADE,
        related_name="measurements",
    )

    measurement_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        db_index=True,
    )

    name = models.CharField(
        max_length=255,
        help_text="Optional user-defined label for the measurement.",
    )

    geometry = models.GeometryField()

    value = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        help_text="Calculated distance or area value.",
    )

    unit = models.CharField(
        max_length=20,
        help_text="Example: m, km, m², hectares.",
    )

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "surveys_measurement"
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["survey"]),
            models.Index(fields=["measurement_type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.measurement_type})"
