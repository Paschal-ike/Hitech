from django.urls import path

from .views import (
    SurveyApproveView,
    SurveyCreateView,
    SurveyDetailView,
    SurveyListView,
    SurveyRejectView,
    SurveyStatusUpdateView,
    SurveySubmitView,
    SurveyUpdateView,
)
from surveys.viewers.views import Survey2DViewerView, Survey3DViewerView
from uploads.views import SurveyViewerDataView

app_name = "surveys"

urlpatterns = [
    path(
        "",
        SurveyListView.as_view(),
        name="survey-list",
    ),
    path(
        "create/",
        SurveyCreateView.as_view(),
        name="survey-create",
    ),
    path(
        "<uuid:pk>/",
        SurveyDetailView.as_view(),
        name="survey-detail",
    ),
    path(
        "<uuid:pk>/edit/",
        SurveyUpdateView.as_view(),
        name="survey-update",
    ),
    path(
        "<uuid:pk>/submit/",
        SurveySubmitView.as_view(),
        name="survey-submit",
    ),
    path(
        "<uuid:pk>/approve/",
        SurveyApproveView.as_view(),
        name="survey-approve",
    ),
    path(
        "<uuid:pk>/reject/",
        SurveyRejectView.as_view(),
        name="survey-reject",
    ),
    path(
        "<uuid:pk>/status/",
        SurveyStatusUpdateView.as_view(),
        name="survey-status",
    ),
    path(
        "<uuid:pk>/2d/",
        Survey2DViewerView.as_view(),
        name="survey-2d-viewer",
    ),
    path(
        "<uuid:pk>/3d/",
        Survey3DViewerView.as_view(),
        name="survey-3d-viewer",
    ),
    path(
        "<uuid:pk>/data/",
        SurveyViewerDataView.as_view(),
        name="survey-viewer-data",
    ),
]
