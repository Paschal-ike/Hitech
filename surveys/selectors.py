from django.db.models import Count

from .models import Survey
from uploads.models import SurveyFile


def get_surveys(*, user):
    queryset = Survey.objects.select_related(
        "project",
        "site",
        "created_by",
        "approved_by",
    ).prefetch_related(
        "files",
        "measurements",
        "upload_sessions",
    )

    if user.is_admin:
        return queryset

    return queryset.filter(
        project__memberships__user=user,
        project__memberships__is_active=True,
    ).distinct()


def get_survey_by_id(*, survey_id, user):
    return get_surveys(
        user=user,
    ).get(
        pk=survey_id,
    )


def get_project_surveys(*, project, user):
    return get_surveys(user=user).filter(project=project)


def get_site_surveys(*, site, user):
    return get_surveys(user=user).filter(site=site)


def get_ready_surveys(*, user):
    return get_surveys(user=user).filter(status=Survey.Status.READY)


def get_recent_surveys(*, user, limit=10):
    return get_surveys(user=user)[:limit]


def get_survey_statistics():
    return {
        "total_surveys": Survey.objects.count(),
        "draft_surveys": Survey.objects.filter(
            status=Survey.Status.DRAFT,
        ).count(),
        "uploading_surveys": Survey.objects.filter(
            status=Survey.Status.UPLOADING,
        ).count(),
        "ready_surveys": Survey.objects.filter(
            status=Survey.Status.READY,
        ).count(),
        "approved_surveys": Survey.objects.filter(
            status=Survey.Status.APPROVED,
        ).count(),
        "archived_surveys": Survey.objects.filter(
            status=Survey.Status.ARCHIVED,
        ).count(),
    }
