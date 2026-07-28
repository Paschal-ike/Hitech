from django.shortcuts import get_object_or_404

from .models import Project, Site


def get_projects():
    return Project.objects.select_related("created_by").prefetch_related(
        "sites", "memberships"
    )


def get_project_by_id(*, project_id):
    return get_object_or_404(
        Project.objects.select_related("created_by"),
        pk=project_id,
    )


def get_sites():
    return Site.objects.select_related("project")


def get_site_by_id(*, site_id):
    return get_object_or_404(
        Site.objects.select_related("project"),
        pk=site_id,
    )


def get_sites_for_project(*, project):
    return Site.objects.filter(project=project).order_by("name")


def get_project_statistics(*, project):
    return {
        "site_count": project.sites.count(),
        "survey_count": project.surveys.count(),
        "member_count": project.memberships.filter(is_active=True).count(),
    }
