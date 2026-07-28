from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)

from accounts.models import ProjectMembership

Role = ProjectMembership.Role


class SurveyAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    required_roles = ()

    def get_project(self):
        survey = self.get_object()
        return survey.project

    def test_func(self):
        user = self.request.user

        if user.is_admin:
            return True

        return user.has_project_role(
            self.get_project(),
            *self.required_roles,
        )


class SurveyViewerMixin(SurveyAccessMixin):
    required_roles = (
        Role.PROJECT_MANAGER,
        Role.SURVEY_ENGINEER,
        Role.VIEWER,
    )


class SurveyEditorMixin(SurveyAccessMixin):
    required_roles = (
        Role.PROJECT_MANAGER,
        Role.SURVEY_ENGINEER,
    )


class SurveyApprovalMixin(SurveyAccessMixin):
    required_roles = (Role.PROJECT_MANAGER,)
