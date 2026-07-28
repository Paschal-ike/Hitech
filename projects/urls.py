from django.urls import path

from .views import (
    ProjectListView,
    ProjectDetailView,
    ProjectCreateView,
    ProjectUpdateView,
    ProjectStatusUpdateView,
    ProjectSiteOptionsView,
    SiteListView,
    SiteDetailView,
    SiteCreateView,
    SiteUpdateView,
)

app_name = "projects"

urlpatterns = [
    # Projects
    path(
        "",
        ProjectListView.as_view(),
        name="project-list",
    ),
    path(
        "create/",
        ProjectCreateView.as_view(),
        name="project-create",
    ),
    path(
        "<uuid:pk>/",
        ProjectDetailView.as_view(),
        name="project-detail",
    ),
    path(
        "<uuid:pk>/edit/",
        ProjectUpdateView.as_view(),
        name="project-update",
    ),
    path(
        "<uuid:pk>/status/",
        ProjectStatusUpdateView.as_view(),
        name="project-status",
    ),
    # Sites
    path(
        "<uuid:project_pk>/sites/",
        SiteListView.as_view(),
        name="site-list",
    ),
    path(
        "<uuid:project_pk>/sites/create/",
        SiteCreateView.as_view(),
        name="site-create",
    ),
    path(
        "sites/<uuid:pk>/",
        SiteDetailView.as_view(),
        name="site-detail",
    ),
    path(
        "sites/<uuid:pk>/edit/",
        SiteUpdateView.as_view(),
        name="site-update",
    ),
    path(
        "<uuid:project_pk>/site-options/",
        ProjectSiteOptionsView.as_view(),
        name="project-site-options",
    ),
]
