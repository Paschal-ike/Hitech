from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
)

from accounts.permissions import (
    ProjectManagerRequiredMixin,
    ProjectMemberRequiredMixin,
)
from accounts.authorization import visible_projects

from .forms import (
    ProjectForm,
    SiteForm,
)
from .models import Project, Site
from .selectors import (
    get_project_by_id,
    get_projects,
    get_site_by_id,
    get_sites_for_project,
)
from .services import (
    create_project,
    create_site,
    update_project,
    update_project_status,
    update_site,
)


from django.db.models import Q
from django.views.generic import ListView


class ProjectListView(ListView):
    template_name = "projects/project_list.html"
    context_object_name = "projects"
    paginate_by = (
        10  # 💡 Optional: Add pagination so your shared/pagination template functions
    )

    def get_queryset(self):
        # 1. First, fetch your authorized baseline projects using your existing service architecture
        queryset = visible_projects(
            get_projects(),
            user=self.request.user,
        )

        # 2. Extract the safe request string from the filter bar template's GET query
        search_query = self.request.GET.get("search", "").strip()

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(project_code__icontains=search_query)
                | Q(client_name__icontains=search_query)
            )

        return queryset


class ProjectDetailView(ProjectMemberRequiredMixin, DetailView):
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_object(self):
        return get_project_by_id(
            project_id=self.kwargs["pk"],
        )

    def get_project(self):
        return self.get_object()


class ProjectCreateView(ProjectManagerRequiredMixin, CreateView):
    form_class = ProjectForm
    template_name = "projects/project_form.html"
    success_url = reverse_lazy("projects:project-list")

    def get_project(self):
        return None

    def test_func(self):
        return self.request.user.is_admin

    def form_valid(self, form):
        create_project(
            created_by=self.request.user,
            data=form.cleaned_data,
        )

        messages.success(
            self.request,
            "Project created successfully.",
        )

        return redirect(self.success_url)


class ProjectUpdateView(ProjectManagerRequiredMixin, UpdateView):
    form_class = ProjectForm
    template_name = "projects/project_form.html"

    def get_object(self):
        return get_project_by_id(
            project_id=self.kwargs["pk"],
        )

    def get_project(self):
        return self.get_object()

    def form_valid(self, form):
        update_project(
            project=self.object,
            data=form.cleaned_data,
        )

        messages.success(
            self.request,
            "Project updated successfully.",
        )

        return redirect(
            reverse(
                "projects:detail",
                kwargs={"pk": self.object.pk},
            )
        )


class ProjectStatusUpdateView(ProjectManagerRequiredMixin, View):
    def get_project(self):
        return get_project_by_id(
            project_id=self.kwargs["pk"],
        )

    def post(self, request, pk):
        project = self.get_project()

        status = request.POST.get("status")

        update_project_status(
            project=project,
            status=status,
        )

        messages.success(
            request,
            f'Project status updated to "{project.get_status_display()}".',
        )

        return HttpResponseRedirect(
            reverse(
                "projects:detail",
                kwargs={"pk": project.pk},
            )
        )


class SiteListView(ProjectMemberRequiredMixin, ListView):
    template_name = "projects/sites/list.html"
    context_object_name = "sites"

    def get_project(self):
        return get_project_by_id(
            project_id=self.kwargs["project_pk"],
        )

    def get_queryset(self):
        return get_sites_for_project(
            project=self.get_project(),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class ProjectSiteOptionsView(ProjectMemberRequiredMixin, View):
    def get_project(self):
        return get_project_by_id(
            project_id=self.kwargs["project_pk"],
        )

    def get(self, request, *args, **kwargs):

        project = self.get_project()

        sites = get_sites_for_project(
            project=project,
        )

        return JsonResponse(
            [
                {
                    "id": str(site.pk),
                    "name": site.name,
                }
                for site in sites
            ],
            safe=False,
        )


class SiteDetailView(ProjectMemberRequiredMixin, DetailView):
    template_name = "projects/sites/detail.html"
    context_object_name = "site"

    def get_object(self):
        return get_site_by_id(
            site_id=self.kwargs["pk"],
        )

    def get_project(self):
        return self.get_object().project


class SiteCreateView(ProjectManagerRequiredMixin, CreateView):
    form_class = SiteForm
    template_name = "projects/sites/create.html"

    def get_project(self):
        return get_project_by_id(
            project_id=self.kwargs["project_pk"],
        )

    def get_initial(self):
        initial = super().get_initial()
        initial["project"] = self.get_project()
        return initial

    def form_valid(self, form):
        create_site(
            project=self.get_project(),
            created_by=self.request.user,
            data=form.cleaned_data,
        )

        messages.success(
            self.request,
            "Site created successfully.",
        )

        return HttpResponseRedirect(
            reverse(
                "projects:site-list",
                kwargs={
                    "project_pk": self.get_project().pk,
                },
            )
        )


class SiteUpdateView(ProjectManagerRequiredMixin, UpdateView):
    form_class = SiteForm
    template_name = "projects/sites/update.html"

    def get_object(self):
        return get_site_by_id(
            site_id=self.kwargs["pk"],
        )

    def get_project(self):
        return self.get_object().project

    def form_valid(self, form):
        update_site(
            site=self.object,
            data=form.cleaned_data,
        )

        messages.success(
            self.request,
            "Site updated successfully.",
        )

        return HttpResponseRedirect(
            reverse(
                "projects:site-detail",
                kwargs={
                    "pk": self.object.pk,
                },
            )
        )
