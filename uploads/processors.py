import mimetypes
import tempfile
import subprocess
import zipfile
import json
from pathlib import Path
from django.db import transaction
from django.conf import settings
from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from celery import chord
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
            generate_tiles(survey_file=survey_file)

        case SurveyFile.FileFormat.MODEL:
            generate_model(survey_file=survey_file)

        case SurveyFile.FileFormat.MESH:
            generate_mesh_model(survey_file=survey_file)

        case SurveyFile.FileFormat.POINT_CLOUD:
            generate_point_cloud(survey_file=survey_file)

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


def generate_tiles(*, survey_file):
    output_directory = (
        Path(settings.MEDIA_ROOT)
        / "surveys"
        / "tiles"
        / str(survey_file.survey_id)
        / str(survey_file.pk)
    )
    output_directory.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        optimized_tiff = Path(temp_dir) / "optimized.tif"

        try:
            subprocess.run(
                [
                    "gdal_translate",
                    survey_file.original_file.path,
                    str(optimized_tiff),
                    "-of", "COG",
                    "-co", "COMPRESS=WEBP",
                    "-co", "QUALITY=85",
                    "-co", "BIGTIFF=YES",
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=900,
            )
            logger.info(
                "Optimized survey file %s into WEBP COG for tiling", survey_file.pk
            )
        except subprocess.CalledProcessError as exc:
            logger.error(
                "gdal_translate optimization failed for survey file %s: %s",
                survey_file.pk, exc.stderr,
            )
            raise

        try:
            result = subprocess.run(
                [
                    "gdal2tiles.py",
                    "--xyz",
                    "--profile=mercator",
                    "-z", "16-20",
                    "--processes=4",
                    str(optimized_tiff),
                    str(output_directory),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=1800,
            )
            logger.info(
                "gdal2tiles.py completed for survey file %s: %s",
                survey_file.pk, result.stdout[-2000:],
            )
        except subprocess.TimeoutExpired:
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

def generate_model(*, survey_file):
    """MODEL format: already .glb/.gltf — just Draco-compress for faster loads."""
    output_directory = (
        Path(settings.MEDIA_ROOT) / "surveys" / "models" / str(survey_file.survey_id)
    )
    output_directory.mkdir(parents=True, exist_ok=True)

    source_path = Path(survey_file.original_file.path)
    final_glb = output_directory / f"{survey_file.pk}.glb"

    subprocess.run(
        ["gltf-pipeline", "-i", str(source_path), "-o", str(final_glb), "-d"],
        check=True, capture_output=True, text=True, timeout=600,
    )

    if not final_glb.exists():
        raise RuntimeError("Model compression produced no output.")

    survey_file.model_path = f"surveys/models/{survey_file.survey_id}/{survey_file.pk}.glb"
    survey_file.save(update_fields=["model_path"])


def generate_mesh_model(*, survey_file):
    """MESH format: always .obj — convert to glTF then Draco-compress."""
    output_directory = (
        Path(settings.MEDIA_ROOT) / "surveys" / "models" / str(survey_file.survey_id)
    )
    output_directory.mkdir(parents=True, exist_ok=True)

    source_path = Path(survey_file.original_file.path)
    intermediate_glb = output_directory / f"{survey_file.pk}_raw.glb"
    final_glb = output_directory / f"{survey_file.pk}.glb"

    subprocess.run(
        ["obj2gltf", "-i", str(source_path), "-o", str(intermediate_glb)],
        check=True, capture_output=True, text=True, timeout=600,
    )
    subprocess.run(
        ["gltf-pipeline", "-i", str(intermediate_glb), "-o", str(final_glb), "-d"],
        check=True, capture_output=True, text=True, timeout=600,
    )
    intermediate_glb.unlink(missing_ok=True)

    if not final_glb.exists():
        raise RuntimeError("Mesh conversion produced no output.")

    survey_file.model_path = f"surveys/models/{survey_file.survey_id}/{survey_file.pk}.glb"
    survey_file.save(update_fields=["model_path"])


def generate_point_cloud(*, survey_file):
    """POINT_CLOUD format: always .las/.laz — build a Potree octree for streaming."""
    output_directory = (
        Path(settings.MEDIA_ROOT)
        / "surveys" / "pointclouds" / str(survey_file.survey_id) / str(survey_file.pk)
    )
    output_directory.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "PotreeConverter",
            survey_file.original_file.path,
            "-o", str(output_directory),
            "--generate-page", "",
        ],
        check=True, capture_output=True, text=True, timeout=1800,
    )

    if not (output_directory / "metadata.json").exists():
        raise RuntimeError("Point cloud conversion produced no output.")

    survey_file.point_cloud_directory = (
        f"surveys/pointclouds/{survey_file.survey_id}/{survey_file.pk}"
    )
    survey_file.save(update_fields=["point_cloud_directory"])