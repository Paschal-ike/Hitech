from .models import SurveyFile, UploadSession


def get_upload_sessions():
    return UploadSession.objects.select_related(
        "survey",
        "uploaded_by",
    )


def get_upload_session_by_id(*, session_id):
    return get_upload_sessions().filter(pk=session_id).first()


def get_survey_files(*, survey=None):
    queryset = SurveyFile.objects.select_related(
        "survey",
        "upload_session",
        "uploaded_by",
    )

    if survey is not None:
        queryset = queryset.filter(
            survey=survey,
        )

    return queryset


def get_survey_file_by_id(*, file_id):
    return get_survey_files().filter(pk=file_id).first()


def get_files_for_survey(*, survey):
    return get_survey_files().filter(survey=survey)


def get_files_by_format(*, survey, file_format):
    return get_files_for_survey(survey=survey).filter(file_format=file_format)


def get_upload_statistics():
    return {
        "total_sessions": UploadSession.objects.count(),
        "total_files": SurveyFile.objects.count(),
        "validated_files": SurveyFile.objects.filter(
            validation_passed=True,
        ).count(),
    }
