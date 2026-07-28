from django.views.generic import (
    DetailView,
)
from surveys.selectors import get_survey_by_id
from surveys.permissions import SurveyViewerMixin
from .selectors import get_latest_orthomosaic, get_latest_model

from django.conf import settings


class Survey2DViewerView(SurveyViewerMixin, DetailView):
    template_name = "surveys/map_viewer.html"
    context_object_name = "survey"

    def get_object(self):
        return get_survey_by_id(
            survey_id=self.kwargs["pk"],
            user=self.request.user,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        orthomosaic = get_latest_orthomosaic(survey=self.object)
        context["orthomosaic"] = orthomosaic

        if self.object.tile_directory:
            context["tile_url_template"] = (
                f"{settings.MEDIA_URL}{self.object.tile_directory}/{{z}}/{{x}}/{{y}}.png"
            )
        else:
            context["tile_url_template"] = None

        return context


class Survey3DViewerView(
    SurveyViewerMixin,
    DetailView,
):
    template_name = "surveys/model_viewer.html"
    context_object_name = "survey"

    def get_object(self):
        return get_survey_by_id(
            survey_id=self.kwargs["pk"],
            user=self.request.user,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        model = get_latest_model(
            survey=self.object,
        )

        context["model"] = model
        context["model_url"] = model.original_file.url if model else None

        return context
