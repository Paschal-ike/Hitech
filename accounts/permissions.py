from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .authorization import (
    can_manage_project,
    can_view_project,
    can_approve_survey,
    can_edit_survey,
)


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin


class ProjectPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    def get_project(self):
        raise NotImplementedError(
            "Views using ProjectPermissionMixin must implement get_project()."
        )


class ProjectManagerRequiredMixin(ProjectPermissionMixin):
    def test_func(self):
        return can_manage_project(
            user=self.request.user,
            project=self.get_project(),
        )


class ProjectMemberRequiredMixin(ProjectPermissionMixin):
    def test_func(self):
        return can_view_project(
            user=self.request.user,
            project=self.get_project(),
        )


class SurveyEditorRequiredMixin(ProjectPermissionMixin):
    def test_func(self):
        return can_edit_survey(
            user=self.request.user,
            project=self.get_project(),
        )


class SurveyApproverRequiredMixin(ProjectPermissionMixin):
    def test_func(self):
        return can_approve_survey(
            user=self.request.user,
            project=self.get_project(),
        )
