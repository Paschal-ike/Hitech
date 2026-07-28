from django.urls import path

from .views import (
    DashboardView,
    LoginView,
    ProfileView,
    UserCreateView,
    UserListView,
    UserLogoutView,
    UserUpdateView,
    UserDetailView,
    UserStatusUpdateView,
)

app_name = "accounts"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/create/", UserCreateView.as_view(), name="user-create"),
    path("users/<uuid:pk>/edit/", UserUpdateView.as_view(), name="user-update"),
    path(
        "users/<uuid:pk>/",
        UserDetailView.as_view(),
        name="user-detail",
    ),
    path(
        "users/<uuid:pk>/status/",
        UserStatusUpdateView.as_view(),
        name="user-status-update",
    ),
]
