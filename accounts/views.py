from django.contrib import messages
from django.contrib.auth.views import LogoutView
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import (
    LoginForm,
    ProfileUpdateForm,
    UserCreateForm,
    UserUpdateForm,
)
from .permissions import AdminRequiredMixin
from .selectors import (
    get_active_users,
    get_user_by_id,
)
from .services import (
    toggle_user_status,
    create_user,
    login_user,
    update_profile,
    update_user,
)


class LoginView(FormView):
    template_name = "accounts/login.html"
    form_class = LoginForm
    success_url = reverse_lazy("accounts:dashboard")

    def form_valid(self, form):
        login_user(
            request=self.request,
            form=form,
        )

        messages.success(
            self.request,
            "Login successful.",
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        for error in form.non_field_errors():
            messages.error(self.request, error)

        return redirect("accounts:login")


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


class DashboardView(AdminRequiredMixin, TemplateView):
    template_name = "accounts/dashboard.html"


class UserListView(AdminRequiredMixin, ListView):
    template_name = "accounts/users/list.html"
    context_object_name = "users"

    def get_queryset(self):
        return get_active_users()


class UserDetailView(AdminRequiredMixin, DetailView):
    template_name = "accounts/users/detail.html"
    context_object_name = "user_object"

    def get_object(self):
        return get_user_by_id(
            user_id=self.kwargs["pk"],
        )


class UserCreateView(AdminRequiredMixin, CreateView):
    form_class = UserCreateForm
    template_name = "accounts/users/create.html"
    success_url = reverse_lazy("accounts:user-list")

    def form_valid(self, form):
        create_user(
            data=form.cleaned_data,
        )

        messages.success(
            self.request,
            "User created successfully.",
        )

        return redirect(self.success_url)


class UserUpdateView(AdminRequiredMixin, UpdateView):
    form_class = UserUpdateForm
    template_name = "accounts/users/update.html"
    success_url = reverse_lazy("accounts:user-list")

    def get_object(self):
        return get_user_by_id(
            user_id=self.kwargs["pk"],
        )

    def form_valid(self, form):
        update_user(
            user=self.object,
            data=form.cleaned_data,
        )

        messages.success(
            self.request,
            "User updated successfully.",
        )

        return redirect(self.success_url)


class UserStatusUpdateView(AdminRequiredMixin, View):
    def post(self, request, pk):
        user = get_user_by_id(user_id=pk)

        is_active = request.POST.get("is_active") == "true"

        toggle_user_status(
            user=user,
            is_active=is_active,
        )

        messages.success(
            request,
            f"{user.get_full_name() or user.username} has been "
            f"{'activated' if is_active else 'deactivated'}.",
        )

        return HttpResponseRedirect(
            reverse(
                "accounts:user-detail",
                kwargs={"pk": user.pk},
            )
        )


class ProfileView(UpdateView):
    form_class = ProfileUpdateForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        update_profile(
            user=self.request.user,
            data=form.cleaned_data,
        )

        messages.success(
            self.request,
            "Profile updated successfully.",
        )

        return redirect(self.success_url)
