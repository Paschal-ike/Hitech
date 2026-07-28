from django import forms

from .models import Project, Site


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = (
            "project_code",
            "name",
            "description",
            "client_name",
            "location",
            "start_date",
            "end_date",
        )

        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError(
                "End date cannot be earlier than the start date."
            )

        return cleaned_data


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = (
            "name",
            "description",
            "location",
            "coordinates",
        )

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "coordinates": forms.HiddenInput(),
        }

    def clean_coordinates(self):
        coordinates = self.cleaned_data.get("coordinates")

        if not coordinates:
            raise forms.ValidationError("Please select a location on the map.")

        return coordinates
