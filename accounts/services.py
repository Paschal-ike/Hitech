from django.contrib.auth import login, logout
from django.db import transaction

from .models import User


@transaction.atomic
def create_user(*, data: dict):
    return User.objects.create_user(**data)


@transaction.atomic
def update_user(*, user: User, data: dict):
    for field, value in data.items():
        setattr(user, field, value)

    user.save()

    return user


@transaction.atomic
def update_profile(*, user: User, data: dict):
    for field, value in data.items():
        setattr(user, field, value)

    user.save()

    return user


def login_user(*, request, form):
    login(request, form.get_user())


def logout_user(*, request):
    logout(request)


@transaction.atomic
def toggle_user_status(*, user: User, is_active: bool):
    user.is_active = is_active
    user.save(update_fields=["is_active"])
