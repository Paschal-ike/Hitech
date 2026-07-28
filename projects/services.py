from django.db import transaction

from .models import Project, Site


@transaction.atomic
def create_project(*, data, created_by):
    return Project.objects.create(
        created_by=created_by,
        **data,
    )


@transaction.atomic
def update_project(*, project, data):
    for field, value in data.items():
        setattr(project, field, value)

    project.save()

    return project


@transaction.atomic
def update_project_status(*, project, status):
    project.status = status
    project.save(update_fields=["status"])

    return project


@transaction.atomic
def create_site(*, project, data, created_by):
    return Site.objects.create(
        project=project,
        created_by=created_by,
        **data,
    )


@transaction.atomic
def update_site(*, site, data):
    for field, value in data.items():
        setattr(site, field, value)

    site.save()

    return site
