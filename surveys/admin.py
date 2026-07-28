from django.contrib import admin

from .models import Measurement, Survey


class MeasurementInline(admin.TabularInline):
    model = Measurement
    extra = 0
    fields = (
        "name",
        "measurement_type",
        "value",
        "unit",
        "created_at",
    )
    readonly_fields = ("created_at",)


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "project",
        "site",
        "survey_date",
        "status",
        "processing_status",
        "approved_by",
    )

    list_filter = (
        "status",
        "processing_status",
        "survey_date",
        "project",
        "site",
    )

    search_fields = (
        "name",
        "description",
        "pilot",
        "drone_model",
    )

    autocomplete_fields = (
        "project",
        "site",
        "created_by",
        "approved_by",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "submitted_at",
        "approved_at",
    )

    ordering = (
        "-survey_date",
        "-created_at",
    )

    inlines = (MeasurementInline,)


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "survey",
        "measurement_type",
        "value",
        "unit",
        "created_at",
    )

    list_filter = (
        "measurement_type",
        "survey",
    )

    search_fields = (
        "name",
        "survey__name",
    )

    autocomplete_fields = (
        "survey",
        "created_by",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)
