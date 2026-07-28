from django.contrib import admin

from .models import (
    UploadSession,
    SurveyFile,
)


@admin.register(UploadSession)
class UploadSessionAdmin(admin.ModelAdmin):
    list_display = (
        "survey",
        "uploaded_by",
        "status",
        "created_at",
        "processing_completed_at",
        "processing_started_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "survey__name",
        "uploaded_by__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "processing_completed_at",
    )


@admin.register(SurveyFile)
class SurveyFileAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename",
        "survey",
        "file_format",
        "file_size",
        "validation_passed",
        "uploaded_by",
        "created_at",
    )

    list_filter = (
        "file_format",
        "validation_passed",
        "created_at",
    )

    search_fields = (
        "original_filename",
        "survey__name",
        "checksum",
    )

    readonly_fields = (
        "checksum",
        "created_at",
        "updated_at",
        "file_size",
        "mime_type",
        "original_filename",
    )
