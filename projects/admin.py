from django.contrib import admin

from .models import Project, Site


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "project_code",
        "name",
        "client_name",
        "status",
        "start_date",
        "end_date",
        "created_by",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "project_code",
        "name",
        "client_name",
        "location",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "project",
        "location",
        "created_at",
    )

    search_fields = (
        "name",
        "project__name",
        "location",
    )

    list_filter = ("project",)

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "project",
        "name",
    )
