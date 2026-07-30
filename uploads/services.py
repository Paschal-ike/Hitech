import hashlib
import mimetypes
from pathlib import Path

from django.db import transaction
from django.utils import timezone

from .models import SurveyFile, UploadSession

from django.conf import settings


def generate_checksum(uploaded_file):
    sha256 = hashlib.sha256()

    for chunk in uploaded_file.chunks():
        sha256.update(chunk)

    uploaded_file.seek(0)

    return sha256.hexdigest()


def normalize_uploaded_file(uploaded_file):

    return {
        "original_file": uploaded_file,
        "original_filename": Path(uploaded_file.name).name,
        "relative_path": uploaded_file.name,
        "file_format": determine_file_format(
            uploaded_file.name,
        ),
        "mime_type": mimetypes.guess_type(
            uploaded_file.name,
        )[0]
        or "",
        "file_size": uploaded_file.size,
        "checksum": generate_checksum(
            uploaded_file,
        ),
        "validation_passed": True,
    }


def start_upload_session(
    *,
    survey,
    uploaded_by,
    uploaded_archive,
):
    return UploadSession.objects.create(
        survey=survey,
        uploaded_by=uploaded_by,
        archive=uploaded_archive,
    )


@transaction.atomic
def save_survey_file(
    *,
    survey,
    upload_session,
    uploaded_by,
    file_data,
):
    return SurveyFile.objects.create(
        survey=survey,
        upload_session=upload_session,
        uploaded_by=uploaded_by,
        **file_data,
    )


@transaction.atomic
def save_uploaded_files(
    *,
    survey,
    upload_session,
    uploaded_by,
    uploaded_files,
):
    """
    Saves multiple uploaded files regardless of whether they came
    from a folder upload or a ZIP extraction.
    """

    saved_files = []

    for uploaded_file in uploaded_files:
        file_data = normalize_uploaded_file(
            uploaded_file,
        )

        saved_files.append(
            save_survey_file(
                survey=survey,
                upload_session=upload_session,
                uploaded_by=uploaded_by,
                file_data=file_data,
            )
        )

    return saved_files


@transaction.atomic
def complete_upload_session(
    *,
    upload_session,
):
    upload_session.status = UploadSession.Status.COMPLETED
    upload_session.completed_at = timezone.now()

    upload_session.save(
        update_fields=[
            "status",
            "completed_at",
        ]
    )

    return upload_session


def determine_file_format(filename):
    name = filename.lower()

    if name.endswith("result.tif") or "orthomosaic" in name:
        return SurveyFile.FileFormat.ORTHOMOSAIC

    if "dsm" in name:
        return SurveyFile.FileFormat.DSM

    if "dtm" in name:
        return SurveyFile.FileFormat.DTM

    if name.endswith(".las") or name.endswith(".laz"):
        return SurveyFile.FileFormat.POINT_CLOUD

    if name.endswith(".glb") or name.endswith(".gltf"):
        return SurveyFile.FileFormat.MODEL

    if name.endswith(".obj"):
        return SurveyFile.FileFormat.MESH

    if name.endswith(".kml"):
        return SurveyFile.FileFormat.KML

    if name.endswith(".geojson"):
        return SurveyFile.FileFormat.GEOJSON

    if name.endswith(".json"):
        return SurveyFile.FileFormat.METADATA

    return SurveyFile.FileFormat.OTHER


@transaction.atomic
def create_survey_file(
    *,
    survey,
    upload_session,
    uploaded_by,
    uploaded_file,
    file_format,
):
    return SurveyFile.objects.create(
        survey=survey,
        upload_session=upload_session,
        uploaded_by=uploaded_by,
        original_file=uploaded_file,
        original_filename=Path(uploaded_file.name).name,
        relative_path=uploaded_file.name,
        file_format=file_format,
        mime_type=(
            mimetypes.guess_type(
                uploaded_file.name,
            )[0]
            or ""
        ),
        file_size=uploaded_file.size,
        checksum=generate_checksum(
            uploaded_file,
        ),
        validation_passed=True,
    )


# uploads/services.py
def get_upload_session_status(*, upload_session_id):
    upload_session = UploadSession.objects.select_related("survey").get(pk=upload_session_id)
    survey = upload_session.survey

    return {
        "status": upload_session.status,
        "status_display": upload_session.get_status_display(),
        "progress": upload_session.progress,
        "processed_files": upload_session.processed_files,
        "total_files": upload_session.total_files,
        "viewer_2d_ready": survey.has_2d_viewer,
        "viewer_3d_ready": survey.has_3d_viewer,
        "processing_complete": upload_session.status == UploadSession.Status.COMPLETED,
        "processing_failed": upload_session.status == UploadSession.Status.FAILED,
    }


def get_survey_viewer_data(*, survey):

    orthomosaics = survey.files.filter(
        status=SurveyFile.Status.COMPLETED,
        file_format=SurveyFile.FileFormat.ORTHOMOSAIC,
    ).exclude(tile_directory="")

    model_files = survey.files.filter(
        status=SurveyFile.Status.COMPLETED,
        file_format__in=[
            SurveyFile.FileFormat.MODEL,
            SurveyFile.FileFormat.MESH,
            SurveyFile.FileFormat.POINT_CLOUD,
        ],
    )

    return {
        "survey_id": survey.pk,
        "orthomosaics": [_serialize_orthomosaic(f) for f in orthomosaics],
        "models": [_serialize_model(f) for f in model_files],
    }


def _serialize_orthomosaic(survey_file):
    return {
        "id": survey_file.pk,
        "name": survey_file.original_filename,
        "tiles_url": (
            f"{settings.MEDIA_URL}{survey_file.tile_directory}/{{z}}/{{x}}/{{y}}.png"
        ),
        "bounds": survey_file.tile_bounds,
    }


def _serialize_model(survey_file):
    return {
        "id": survey_file.pk,
        "name": survey_file.original_filename,
        "format": survey_file.file_format,
        "url": survey_file.original_file.url,
    }
