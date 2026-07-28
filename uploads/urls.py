from django.urls import path

from .views import (
    SurveyFileListView,
    SurveyFileDetailView,
    SurveyFileUploadView,
    SurveyViewerDataView,
    UploadSessionStatusView,
)

app_name = "uploads"

urlpatterns = [
    path(
        "survey/<uuid:survey_pk>/",
        SurveyFileListView.as_view(),
        name="file-list",
    ),
    path(
        "<uuid:pk>/",
        SurveyFileDetailView.as_view(),
        name="file-detail",
    ),
    path(
        "survey/<uuid:survey_pk>/upload/",
        SurveyFileUploadView.as_view(),
        name="file-upload",
    ),
    path(
        "upload-session/<uuid:upload_session_id>/status/",
        UploadSessionStatusView.as_view(),
        name="upload-session-status",
    ),
]
