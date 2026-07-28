from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models

from core.models import TimeStampedModel, UUIDModel


class User(AbstractUser, UUIDModel, TimeStampedModel):
    class Meta:
        db_table = "accounts_user"
        ordering = ["first_name", "last_name", "username"]

    @property
    def is_admin(self):
        return self.is_superuser or self.is_staff

    def has_project_role(self, project, *roles):
        return self.project_memberships.filter(
            project=project,
            role__in=roles,
            is_active=True,
        ).exists()

    def __str__(self):
        return self.get_full_name() or self.username


class ProjectMembership(TimeStampedModel):
    class Role(models.TextChoices):
        PROJECT_MANAGER = "PROJECT_MANAGER", "Project Manager"
        SURVEY_ENGINEER = "SURVEY_ENGINEER", "Survey Engineer"
        VIEWER = "VIEWER", "Viewer"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )

    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        db_index=True,
    )

    is_active = models.BooleanField(default=True)

    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="User who assigned this member to the project.",
    )

    class Meta:
        db_table = "accounts_project_membership"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="unique_project_membership",
            )
        ]
        indexes = [
            models.Index(fields=["project"]),
            models.Index(fields=["user"]),
            models.Index(fields=["role"]),
            models.Index(fields=["project", "user"]),
        ]
        ordering = ["project", "user"]

    def __str__(self):
        return f"{self.user} → {self.project} ({self.get_role_display()})"
