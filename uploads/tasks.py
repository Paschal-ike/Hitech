from celery import shared_task, group, chord
import logging

from .models import SurveyFile, UploadSession
from surveys.models import Survey
from .processors import import_zip_archive, process_uploaded_file

logger = logging.getLogger(__name__)


@shared_task
def process_upload_session_task(upload_session_id):
    """Entry point: extract the archive, then fan out one task per file."""
    upload_session = UploadSession.objects.select_related(
        "survey",
        "uploaded_by",
    ).get(pk=upload_session_id)
    survey = upload_session.survey

    survey.processing_status = Survey.ProcessingStatus.PROCESSING
    survey.save(update_fields=["processing_status"])

    upload_session.status = UploadSession.Status.PROCESSING
    upload_session.progress = 0
    upload_session.current_step = "Extracting archive..."
    upload_session.save(update_fields=["status", "progress", "current_step"])

    try:
        imported_files = import_zip_archive(
            survey=survey,
            upload_session=upload_session,
            uploaded_by=upload_session.uploaded_by,
            uploaded_archive=upload_session.archive,
        )
    except Exception:
        logger.exception("Archive extraction failed for session %s", upload_session.pk)
        _mark_session_failed(upload_session, survey, "Archive extraction failed.")
        return

    if not imported_files:
        _mark_session_failed(upload_session, survey, "No supported files found.")
        return

    file_tasks = group(process_survey_file_task.s(f.pk) for f in imported_files)
    chord(file_tasks)(
        finalize_upload_session_task.s(upload_session_id).on_error(
            finalize_upload_session_error.s(upload_session_id)
        )
    )


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_survey_file_task(self, survey_file_id):
    try:
        survey_file = SurveyFile.objects.select_related("survey").get(pk=survey_file_id)
        process_uploaded_file(survey_file=survey_file)
    except SurveyFile.DoesNotExist:
        logger.error("Survey file %s not found", survey_file_id)
        return {"id": survey_file_id, "ok": False}
    except Exception as exc:
        logger.exception("Processing failed for survey file %s", survey_file_id)
        SurveyFile.objects.filter(pk=survey_file_id).update(
            status=SurveyFile.Status.FAILED,
            error_message=str(exc)[:500],
        )
        return {"id": survey_file_id, "ok": False}

    survey_file.status = SurveyFile.Status.COMPLETED
    survey_file.save(update_fields=["status"])
    return {"id": survey_file_id, "ok": True}


@shared_task
def finalize_upload_session_task(results, upload_session_id):
    """Chord callback — runs once every file task has finished, pass or fail."""
    upload_session = UploadSession.objects.select_related("survey").get(
        pk=upload_session_id
    )
    survey = upload_session.survey
    failed = [r for r in results if not r["ok"]]

    if not failed:
        status, step = UploadSession.Status.COMPLETED, "Completed"
    elif len(failed) == len(results):
        status, step = UploadSession.Status.FAILED, "Processing failed."
    else:
        status, step = (
            UploadSession.Status.COMPLETED_WITH_ERRORS,
            f"{len(failed)} file(s) failed.",
        )

    upload_session.status = status
    upload_session.progress = 100
    upload_session.current_step = step
    upload_session.save(update_fields=["status", "progress", "current_step"])

    survey.processing_status = (
        Survey.ProcessingStatus.FAILED
        if status == UploadSession.Status.FAILED
        else Survey.ProcessingStatus.COMPLETED
    )
    survey.status = Survey.Status.READY
    survey.save(update_fields=["processing_status", "status"])


@shared_task
def finalize_upload_session_error(request, exc, traceback, upload_session_id):
    logger.error("Chord failed for upload session %s: %s", upload_session_id, exc)
    upload_session = UploadSession.objects.select_related("survey").get(
        pk=upload_session_id
    )
    _mark_session_failed(
        upload_session, upload_session.survey, "Processing failed unexpectedly."
    )


def _mark_session_failed(upload_session, survey, message):
    upload_session.status = UploadSession.Status.FAILED
    upload_session.current_step = message
    upload_session.save(update_fields=["status", "current_step"])
    survey.processing_status = Survey.ProcessingStatus.FAILED
    survey.save(update_fields=["processing_status"])
