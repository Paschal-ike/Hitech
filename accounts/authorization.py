from accounts.models import ProjectMembership


Role = ProjectMembership.Role


def is_project_member(*, user, project) -> bool:
    """
    Returns True if the user is an active member of the project.
    """
    if not user.is_authenticated:
        return False

    if user.is_admin:
        return True

    return user.project_memberships.filter(
        project=project,
        is_active=True,
    ).exists()


def has_project_role(user, project, *roles) -> bool:
    """
    Returns True if the user has one of the supplied roles
    within the project.
    """
    if not user.is_authenticated:
        return False

    if user.is_admin:
        return True

    return user.project_memberships.filter(
        project=project,
        role__in=roles,
        is_active=True,
    ).exists()


def can_view_project(*, user, project) -> bool:
    return is_project_member(
        user=user,
        project=project,
    )


def can_manage_project(user, project) -> bool:
    return has_project_role(
        user,
        project,
        Role.PROJECT_MANAGER,
    )


def can_edit_survey(user, project) -> bool:
    return has_project_role(
        user,
        project,
        Role.PROJECT_MANAGER,
        Role.SURVEY_ENGINEER,
    )


def can_upload_files(*, user, project) -> bool:
    """
    Users allowed to upload survey deliverables.
    """
    return can_edit_survey(
        user=user,
        project=project,
    )


def can_process_survey(*, user, project) -> bool:
    """
    Users allowed to start or manage processing jobs.
    """
    return can_edit_survey(
        user=user,
        project=project,
    )


def can_view_files(*, user, project) -> bool:
    """
    Any project member can view uploaded files.
    """
    return can_view_project(
        user=user,
        project=project,
    )


def can_approve_survey(*, user, project) -> bool:
    return can_manage_project(
        user=user,
        project=project,
    )


def visible_projects(queryset, *, user):
    """
    Restrict a queryset to projects visible to the user.
    """
    if not user.is_authenticated:
        return queryset.none()

    if user.is_admin:
        return queryset

    return queryset.filter(
        memberships__user=user,
        memberships__is_active=True,
    ).distinct()
