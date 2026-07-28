from django.db import transaction
from django.utils import timezone

from .models import Survey


@transaction.atomic
def create_survey(*, data, created_by):
    return Survey.objects.create(
        created_by=created_by,
        **data,
    )


@transaction.atomic
def update_survey(*, survey, data):
    for field, value in data.items():
        setattr(survey, field, value)

    survey.save()

    return survey


@transaction.atomic
def submit_survey(*, survey):
    survey.status = Survey.Status.UPLOADING
    survey.submitted_at = timezone.now()

    survey.save(
        update_fields=[
            "status",
            "submitted_at",
        ]
    )

    return survey


@transaction.atomic
def approve_survey(*, survey, approved_by, notes=""):
    survey.status = Survey.Status.APPROVED
    survey.approved_by = approved_by
    survey.approved_at = timezone.now()

    if notes:
        survey.notes = notes

    survey.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
            "notes",
        ]
    )

    return survey


@transaction.atomic
def reject_survey(*, survey, rejection_reason, notes=""):
    survey.status = Survey.Status.DRAFT
    survey.rejection_reason = rejection_reason

    if notes:
        survey.notes = notes

    survey.save(
        update_fields=[
            "status",
            "rejection_reason",
            "notes",
        ]
    )

    return survey


@transaction.atomic
def update_survey_status(*, survey, status):
    survey.status = status

    survey.save(update_fields=["status"])

    return survey


@transaction.atomic
def update_processing_status(*, survey, status):
    survey.processing_status = status

    survey.save(update_fields=["processing_status"])

    return survey
