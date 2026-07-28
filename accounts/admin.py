from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ProjectMembership


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
    )

    list_filter = ("is_staff", "is_superuser", "is_active", "groups")

    search_fields = ("username", "first_name", "last_name", "email")

    ordering = ["first_name", "last_name", "username"]


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "role", "is_active", "created_at", "added_by")

    list_filter = ("role", "is_active", "project")

    autocomplete_fields = ["user", "project", "added_by"]

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "project__name",
    )

    ordering = ["project", "user"]
