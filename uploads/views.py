from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse

from django.views import View
from django.views.generic import (
    FormView,
    DetailView,
    ListView,
)

from accounts.permissions import LoginRequiredMixin

from surveys.selectors import get_survey_by_id
from surveys.models import Survey
from .forms import SurveyFileUploadForm
from .permissions import (
    user_can_upload_files,
)
from .selectors import (
    get_survey_file_by_id,
    get_survey_files,
)
from .services import (
    get_upload_session_status,
    start_upload_session,
    get_survey_viewer_data,
)
from .tasks import process_upload_session_task


class SurveyFileListView(
    LoginRequiredMixin,
    ListView,
):
    template_name = "uploads/file_list.html"
    context_object_name = "files"

    def get_queryset(self):
        self.survey = get_survey_by_id(
            survey_id=self.kwargs["survey_pk"],
            user=self.request.user,
        )

        return get_survey_files(
            survey=self.survey,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["survey"] = self.survey
        return context


class SurveyFileDetailView(LoginRequiredMixin, DetailView):
    template_name = "uploads/file_detail.html"
    context_object_name = "file"

    def get_object(self):
        return get_survey_file_by_id(
            file_id=self.kwargs["pk"],
        )


class SurveyFileUploadView(
    LoginRequiredMixin,
    FormView,
):
    form_class = SurveyFileUploadForm
    template_name = "uploads/upload.html"

    def dispatch(
        self,
        request,
        *args,
        **kwargs,
    ):
        self.survey = get_survey_by_id(
            survey_id=kwargs["survey_pk"],
            user=request.user,
        )

        if not user_can_upload_files(
            request.user,
            self.survey,
        ):
            return redirect(
                "accounts:dashboard",
            )

        return super().dispatch(
            request,
            *args,
            **kwargs,
        )

    def get_context_data(
        self,
        **kwargs,
    ):
        context = super().get_context_data(
            **kwargs,
        )

        context["survey"] = self.survey

        return context

    def form_valid(
        self,
        form,
    ):
        upload_session = start_upload_session(
            survey=self.survey,
            uploaded_by=self.request.user,
            uploaded_archive=form.cleaned_data["archive"],
        )

        process_upload_session_task.delay(
            upload_session.pk,
        )

        messages.success(self.request, "Upload received. Processing has started.")

        return redirect(
            "surveys:survey-detail",
            self.survey.pk,
        )


class UploadSessionStatusView(
    LoginRequiredMixin,
    View,
):
    def get(
        self,
        request,
        upload_session_id,
    ):
        status = get_upload_session_status(
            upload_session_id=upload_session_id,
        )

        return JsonResponse(status)


class SurveyViewerDataView(View):
    def get(self, request, pk, *args, **kwargs):
        survey = get_object_or_404(Survey, pk=pk)
        data = get_survey_viewer_data(survey=survey)
        return JsonResponse(data)
