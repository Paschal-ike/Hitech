from django.contrib.gis.db import models
from core.models import CreatedByModel, TimeStampedModel, UUIDModel


class Project(UUIDModel, TimeStampedModel, CreatedByModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        ARCHIVED = "ARCHIVED", "Archived"

    project_code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique internal project identifier.",
    )

    name = models.CharField(max_length=255)

    description = models.TextField(
        blank=True,
    )

    client_name = models.CharField(
        max_length=255,
        help_text="Client or organization the project is being executed for.",
    )

    location = models.CharField(
        max_length=255,
        help_text="General location of the project.",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    start_date = models.DateField(
        null=True,
        blank=True,
    )

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "projects_project"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project_code"]),
            models.Index(fields=["name"]),
            models.Index(fields=["status"]),
            models.Index(fields=["client_name"]),
        ]

    def __str__(self):
        return f"{self.project_code} - {self.name}"


class Site(UUIDModel, TimeStampedModel, CreatedByModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="sites",
    )

    name = models.CharField(max_length=255)

    description = models.TextField(
        blank=True,
    )

    location = models.CharField(
        max_length=255,
        help_text="Specific location or address of the site.",
    )

    coordinates = models.PointField(
        geography=True,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "projects_site"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"],
                name="unique_site_per_project",
            )
        ]

    def __str__(self):
        return f"{self.project.name} - {self.name}"
