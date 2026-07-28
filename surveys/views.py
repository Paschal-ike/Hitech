from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import (
    SurveyApprovalForm,
    SurveyCreateForm,
    SurveyRejectionForm,
    SurveyUpdateForm,
)
from .models import Survey
from accounts.models import ProjectMembership

from .permissions import (
    SurveyApprovalMixin,
    SurveyEditorMixin,
    SurveyViewerMixin,
)
from accounts.permissions import LoginRequiredMixin
from .selectors import (
    get_survey_by_id,
    get_surveys,
)
from .services import (
    approve_survey,
    create_survey,
    reject_survey,
    submit_survey,
    update_survey,
    update_survey_status,
)

Role = ProjectMembership.Role


class SurveyListView(LoginRequiredMixin, ListView):
    template_name = "surveys/list.html"
    context_object_name = "surveys"

    def get_queryset(self):
        return get_surveys(
            user=self.request.user,
        )


class SurveyDetailView(SurveyViewerMixin, DetailView):
    template_name = "surveys/detail.html"
    context_object_name = "survey"

    def get_object(self):
        return get_survey_by_id(
            survey_id=self.kwargs["pk"],
            user=self.request.user,
        )


class SurveyCreateView(LoginRequiredMixin, CreateView):
    form_class = SurveyCreateForm
    template_name = "surveys/create.html"
    success_url = reverse_lazy("surveys:survey-list")

    def form_valid(self, form):

        project = form.cleaned_data["project"]

        if not self.request.user.is_admin and not self.request.user.has_project_role(
            project,
            Role.PROJECT_MANAGER,
            Role.SURVEY_ENGINEER,
        ):
            return HttpResponseForbidden()

        create_survey(
            data=form.cleaned_data,
            created_by=self.request.user,
        )

        messages.success(
            self.request,
            "Survey created successfully.",
        )

        return redirect(self.success_url)


class SurveyUpdateView(SurveyEditorMixin, UpdateView):
    form_class = SurveyUpdateForm
    template_name = "surveys/update.html"
    success_url = reverse_lazy("surveys:survey-list")

    def get_object(self):
        return get_survey_by_id(
            survey_id=self.kwargs["pk"],
            user=self.request.user,
        )

    def form_valid(self, form):
        update_survey(
            survey=self.object,
            data=form.cleaned_data,
        )

        messages.success(
            self.request,
            "Survey updated successfully.",
        )

        return redirect(self.success_url)


class SurveySubmitView(SurveyEditorMixin, View):
    def post(self, request, pk):
        survey = get_survey_by_id(
            survey_id=pk,
            user=request.user,
        )

        submit_survey(
            survey=survey,
        )

        messages.success(
            request,
            "Survey submitted successfully.",
        )

        return HttpResponseRedirect(
            reverse(
                "surveys:survey-detail",
                kwargs={"pk": survey.pk},
            )
        )


class SurveyApproveView(SurveyApprovalMixin, View):
    def post(self, request, pk):
        survey = get_survey_by_id(
            survey_id=pk,
            user=request.user,
        )

        form = SurveyApprovalForm(request.POST)

        if form.is_valid():
            approve_survey(
                survey=survey,
                approved_by=request.user,
                notes=form.cleaned_data["notes"],
            )

            messages.success(
                request,
                "Survey approved successfully.",
            )

        return HttpResponseRedirect(
            reverse(
                "surveys:survey-detail",
                kwargs={"pk": survey.pk},
            )
        )


class SurveyRejectView(SurveyApprovalMixin, View):
    def post(self, request, pk):
        survey = get_survey_by_id(
            survey_id=pk,
            user=request.user,
        )

        form = SurveyRejectionForm(request.POST)

        if form.is_valid():
            reject_survey(
                survey=survey,
                rejection_reason=form.cleaned_data["rejection_reason"],
                notes=form.cleaned_data["notes"],
            )

            messages.success(
                request,
                "Survey rejected.",
            )

        return HttpResponseRedirect(
            reverse(
                "surveys:survey-detail",
                kwargs={"pk": survey.pk},
            )
        )


class SurveyStatusUpdateView(SurveyApprovalMixin, View):
    def post(self, request, pk):
        survey = get_survey_by_id(
            survey_id=pk,
            user=request.user,
        )

        status = request.POST.get("status")

        if status in Survey.Status.values:
            update_survey_status(
                survey=survey,
                status=status,
            )

            messages.success(
                request,
                "Survey status updated.",
            )

        return HttpResponseRedirect(
            reverse(
                "surveys:survey-detail",
                kwargs={"pk": survey.pk},
            )
        )
