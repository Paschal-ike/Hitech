from rest_framework import permissions

from accounts.models import ProjectMembership

Role = ProjectMembership.Role


def _active_membership(user, project):
    if not user.is_authenticated:
        return None
    return (
        user.project_memberships.filter(project=project, is_active=True)
        .only("role")
        .first()
    )


def user_can_view_project(user, project):
    """Admin, or any active member of the project (any role)."""
    if not user.is_authenticated:
        return False
    if user.is_admin:
        return True
    return _active_membership(user, project) is not None


def user_can_manage_project(user, project):
    """Create/edit project metadata, manage membership: Admin or PM."""
    if not user.is_authenticated:
        return False
    if user.is_admin:
        return True
    membership = _active_membership(user, project)
    return membership is not None and membership.role == Role.PROJECT_MANAGER


def user_can_edit_survey_data(user, project):
    """Upload files / create surveys: Admin, PM, or Survey Engineer."""
    if not user.is_authenticated:
        return False
    if user.is_admin:
        return True
    membership = _active_membership(user, project)
    return membership is not None and membership.role in (
        Role.PROJECT_MANAGER,
        Role.SURVEY_ENGINEER,
    )


def user_can_approve_survey(user, project):
    """Approve/reject a survey: Admin or PM only."""
    return user_can_manage_project(user, project)


def visible_projects_for_user(user, queryset=None):

    from projects.models import Project

    qs = queryset if queryset is not None else Project.objects.all()

    if not user.is_authenticated:
        return qs.none()
    if user.is_admin:
        return qs

    return qs.filter(
        memberships__user=user,
        memberships__is_active=True,
    ).distinct()


# ---------------------------------------------------------------------------
# DRF permission classes
# ---------------------------------------------------------------------------


class IsAuthenticatedAndActive(permissions.BasePermission):
    """Base check: logged in and account not deactivated."""

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_active
        )


class IsProjectMember(IsAuthenticatedAndActive):
    def has_object_permission(self, request, view, obj):
        project = self._resolve_project(obj)
        if project is None:
            return False
        return user_can_view_project(request.user, project)

    @staticmethod
    def _resolve_project(obj):
        from projects.models import Project

        if isinstance(obj, Project):
            return obj
        if hasattr(obj, "project"):
            return obj.project
        # e.g. SurveyFile -> Survey -> Project
        if hasattr(obj, "survey"):
            return obj.survey.project
        return None


class IsProjectManagerOrAdmin(IsProjectMember):
    """Write access to project metadata / membership management."""

    def has_object_permission(self, request, view, obj):
        project = self._resolve_project(obj)
        if project is None:
            return False
        if request.method in permissions.SAFE_METHODS:
            return user_can_view_project(request.user, project)
        return user_can_manage_project(request.user, project)


class CanEditSurveyData(IsProjectMember):
    """Write access for survey/file creation (PM, Survey Engineer, Admin)."""

    def has_object_permission(self, request, view, obj):
        project = self._resolve_project(obj)
        if project is None:
            return False
        if request.method in permissions.SAFE_METHODS:
            return user_can_view_project(request.user, project)
        return user_can_edit_survey_data(request.user, project)


class CanApproveSurvey(IsProjectMember):
    """Approval endpoint guard."""

    def has_object_permission(self, request, view, obj):
        project = self._resolve_project(obj)
        if project is None:
            return False
        return user_can_approve_survey(request.user, project)


class IsAdminOnly(IsAuthenticatedAndActive):
    """Hard gate for admin-only endpoints (e.g. audit log export)."""

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_admin
