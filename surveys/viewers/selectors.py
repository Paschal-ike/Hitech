from uploads.models import SurveyFile


def get_latest_orthomosaic(*, survey):
    return (
        SurveyFile.objects.filter(
            survey=survey,
            file_format=SurveyFile.FileFormat.ORTHOMOSAIC,
        )
        .order_by("-created_at")
        .first()
    )


def get_latest_model(*, survey):
    return (
        SurveyFile.objects.filter(
            survey=survey,
            file_format=SurveyFile.FileFormat.MODEL,
        )
        .order_by("-created_at")
        .first()
    )
