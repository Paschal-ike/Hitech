from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.gis.db import models

from core.models import TimeStampedModel, UUIDModel
from uploads.models import SurveyFile


class ProcessingJob(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    survey_file = models.OneToOneField(
        SurveyFile,
        on_delete=models.CASCADE,
        related_name="processing_job",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    progress = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    retry_count = models.PositiveSmallIntegerField(
        default=0,
    )

    celery_task_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    error_message = models.TextField(
        blank=True,
    )

    output_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Processing results such as preview paths, extracted metadata, etc.",
    )

    class Meta:
        db_table = "processing_processing_job"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.survey_file.original_filename} ({self.status})"
