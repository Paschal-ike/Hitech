from accounts.authorization import (
    can_upload_files,
    can_view_files,
)


def user_can_upload_files(user, survey):
    return can_upload_files(
        user=user,
        project=survey.project,
    )


def user_can_view_file(user, survey_file):
    return can_view_files(
        user=user,
        project=survey_file.survey.project,
    )
