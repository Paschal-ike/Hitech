from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

User = get_user_model()


def get_user_by_id(user_id):
    return get_object_or_404(User, pk=user_id)


def get_user_by_username(username):
    return get_object_or_404(User, username=username)


def get_active_users():
    return User.objects.filter(
        is_active=True,
    ).order_by("first_name", "last_name")


def get_users_by_role(role):
    return User.objects.filter(
        role=role,
        is_active=True,
    ).order_by("first_name", "last_name")


def get_all_users():
    return User.objects.all().order_by(
        "first_name",
        "last_name",
    )
