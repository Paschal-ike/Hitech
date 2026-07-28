import mimetypes
import shutil
import subprocess
import zipfile
import json
from pathlib import Path
from django.db import transaction
from django.conf import settings
from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from surveys.models import Survey
from .models import (
    SurveyFile,
    UploadSession,
)
from .services import (
    create_survey_file,
    determine_file_format,
)

import logging

logger = logging.getLogger(__name__)


def import_zip_archive(
    *,
    survey,
    upload_session,
    uploaded_by,
    uploaded_archive,
):
    imported_files = []

    uploaded_archive.seek(0)

    with zipfile.ZipFile(uploaded_archive) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue

            file_format = determine_file_format(
                member.filename,
            )

            if file_format == SurveyFile.FileFormat.OTHER:
                logger.info(
                    "Skipping unsupported file %r in survey %s upload session %s",
                    member.filename,
                    survey.pk,
                    upload_session.pk,
                )
                continue

            with archive.open(member) as fp:
                uploaded_file = SimpleUploadedFile(
                    name=member.filename,
                    content=fp.read(),
                    content_type=(
                        mimetypes.guess_type(
                            member.filename,
                        )[0]
                        or "application/octet-stream"
                    ),
                )

            survey_file = create_survey_file(
                survey=survey,
                upload_session=upload_session,
                uploaded_by=uploaded_by,
                uploaded_file=uploaded_file,
                file_format=file_format,
            )
            imported_files.append(survey_file)

    logger.info(
        "Imported %d file(s) from archive for survey %s upload session %s",
        len(imported_files),
        survey.pk,
        upload_session.pk,
    )

    return imported_files


def process_uploaded_file(
    *,
    survey_file,
):
    logger.info(
        "Processing survey file %s (%s) format=%s",
        survey_file.pk,
        survey_file.original_filename,
        survey_file.file_format,
    )

    match survey_file.file_format:
        case SurveyFile.FileFormat.ORTHOMOSAIC:
            generate_tiles(
                survey_file=survey_file,
            )

        case (
            SurveyFile.FileFormat.MODEL
            | SurveyFile.FileFormat.MESH
            | SurveyFile.FileFormat.POINT_CLOUD
        ):
            generate_model(
                survey_file=survey_file,
            )

        case SurveyFile.FileFormat.DSM:
            pass

        case SurveyFile.FileFormat.DTM:
            pass

        case SurveyFile.FileFormat.METADATA:
            pass

        case SurveyFile.FileFormat.KML:
            pass

        case SurveyFile.FileFormat.GEOJSON:
            pass

        case _:
            pass


@transaction.atomic
def process_upload_session(
    *,
    upload_session_id,
):
    upload_session = UploadSession.objects.select_related(
        "survey",
        "uploaded_by",
    ).get(
        pk=upload_session_id,
    )

    survey = upload_session.survey

    logger.info(
        "Starting upload session %s for survey %s",
        upload_session.pk,
        survey.pk,
    )

    survey.processing_status = Survey.ProcessingStatus.PROCESSING

    survey.save(
        update_fields=[
            "processing_status",
        ],
    )

    upload_session.status = UploadSession.Status.PROCESSING

    upload_session.progress = 0

    upload_session.current_step = "Extracting archive..."

    upload_session.save(
        update_fields=[
            "status",
            "progress",
            "current_step",
        ],
    )

    try:
        imported_files = import_zip_archive(
            survey=survey,
            upload_session=upload_session,
            uploaded_by=upload_session.uploaded_by,
            uploaded_archive=upload_session.archive,
        )

        total_files = len(imported_files)

        if total_files == 0:
            raise RuntimeError("No supported files found.")

        for index, survey_file in enumerate(
            imported_files,
            start=1,
        ):
            upload_session.current_step = f"Processing {survey_file.original_filename}"

            upload_session.progress = int(((index - 1) / total_files) * 100)

            upload_session.save(
                update_fields=[
                    "progress",
                    "current_step",
                ],
            )

            process_uploaded_file(
                survey_file=survey_file,
            )

        upload_session.status = UploadSession.Status.COMPLETED

        upload_session.progress = 100

        upload_session.current_step = "Completed"

        upload_session.save(
            update_fields=[
                "status",
                "progress",
                "current_step",
            ],
        )

        survey.processing_status = Survey.ProcessingStatus.COMPLETED

        survey.status = Survey.Status.READY

        survey.save(
            update_fields=[
                "processing_status",
                "status",
            ],
        )

        logger.info(
            "Completed upload session %s for survey %s (%d files)",
            upload_session.pk,
            survey.pk,
            total_files,
        )

    except Exception:
        logger.exception(
            "Upload session %s failed for survey %s",
            upload_session.pk,
            survey.pk,
        )

        upload_session.status = UploadSession.Status.FAILED

        upload_session.current_step = "Processing failed."

        upload_session.save(
            update_fields=[
                "status",
                "current_step",
            ],
        )

        survey.processing_status = Survey.ProcessingStatus.FAILED

        survey.save(
            update_fields=[
                "processing_status",
            ],
        )

        raise


def generate_tiles(*, survey_file):
    output_directory = (
        Path(settings.MEDIA_ROOT)
        / "surveys"
        / "tiles"
        / str(survey_file.survey_id)
        / str(survey_file.pk)
    )
    output_directory.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            [
                "gdal2tiles.py",
                "--xyz",
                "--profile=mercator",
                "-z",
                "16-20",
                "--processes=4",
                survey_file.original_file.path,
                str(output_directory),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=1800,
        )
    except subprocess.TimeoutExpired as exc:
        logger.error("gdal2tiles.py timed out for survey file %s", survey_file.pk)
        raise
    except subprocess.CalledProcessError as exc:
        logger.error(
            "gdal2tiles.py failed for survey file %s: %s", survey_file.pk, exc.stderr
        )
        raise
    generated_files = list(output_directory.rglob("*"))
    if not generated_files:
        raise RuntimeError("Tile generation produced no output.")

    bounds = None
    try:
        result = subprocess.run(
            ["gdalinfo", "-json", "-proj4", survey_file.original_file.path],
            check=True,
            capture_output=True,
            text=True,
        )
        info = json.loads(result.stdout)
        corners = info["wgs84Extent"]["coordinates"][0]
        lngs = [c[0] for c in corners]
        lats = [c[1] for c in corners]
        bounds = {
            "south": min(lats),
            "north": max(lats),
            "west": min(lngs),
            "east": max(lngs),
        }
    except Exception:
        logger.warning(
            "Could not extract bounds for survey file %s", survey_file.pk, exc_info=True
        )

    survey_file.tile_directory = (
        f"surveys/tiles/{survey_file.survey_id}/{survey_file.pk}"
    )
    survey_file.tile_bounds = bounds
    survey_file.save(update_fields=["tile_directory", "tile_bounds"])

    logger.info(
        "Generated %d tile file(s) for survey file %s",
        len(generated_files),
        survey_file.pk,
    )


def generate_model(
    *,
    survey_file,
):
    output_directory = (
        Path(settings.MEDIA_ROOT) / "surveys" / "models" / str(survey_file.survey_id)
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = output_directory / Path(survey_file.original_file.name).name

    shutil.copy2(
        survey_file.original_file.path,
        destination,
    )

    if not destination.exists():
        raise RuntimeError("Model generation failed.")

    survey = survey_file.survey

    survey.model_directory = f"surveys/models/{survey.pk}"

    survey.save(
        update_fields=[
            "model_directory",
        ],
    )

    logger.info(
        "Generated model output for survey %s at %s",
        survey.pk,
        destination,
    )
