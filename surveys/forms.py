from django import forms
from django.contrib.gis.geos import GEOSGeometry

from .models import Survey


class SurveyCreateForm(forms.ModelForm):
    class Meta:
        model = Survey

        fields = (
            "project",
            "site",
            "name",
            "description",
            "survey_date",
            "drone_model",
            "pilot",
            "coordinate_reference_system",
            "boundary",
            "notes",
        )

        widgets = {
            "survey_date": forms.DateInput(
                attrs={"type": "date"},
            ),
            "description": forms.Textarea(
                attrs={"rows": 3},
            ),
            "notes": forms.Textarea(
                attrs={"rows": 3},
            ),
            "boundary": forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()

        project = cleaned_data.get("project")
        site = cleaned_data.get("site")

        if project and site and site.project_id != project.id:
            raise forms.ValidationError(
                "The selected site does not belong to the selected project."
            )

        return cleaned_data

    def clean_boundary(self):
        value = self.data.get("boundary")

        if not value:
            raise forms.ValidationError("Please draw the survey boundary.")

        try:
            return GEOSGeometry(value)
        except Exception:
            raise forms.ValidationError("Invalid survey boundary.")


class SurveyUpdateForm(forms.ModelForm):
    class Meta:
        model = Survey

        fields = (
            "site",
            "name",
            "description",
            "survey_date",
            "drone_model",
            "pilot",
            "coordinate_reference_system",
            "boundary",
            "notes",
        )

        widgets = {
            "survey_date": forms.DateInput(
                attrs={"type": "date"},
            ),
            "description": forms.Textarea(
                attrs={"rows": 3},
            ),
            "notes": forms.Textarea(
                attrs={"rows": 3},
            ),
            "boundary": forms.HiddenInput(),
        }

    def clean_boundary(self):
        value = self.data.get("boundary")

        if not value:
            raise forms.ValidationError("Please draw the survey boundary.")

        try:
            return GEOSGeometry(value)
        except Exception:
            raise forms.ValidationError("Invalid survey boundary.")


class SurveyApprovalForm(forms.ModelForm):
    class Meta:
        model = Survey

        fields = ("notes",)

        widgets = {
            "notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Optional approval comments...",
                },
            ),
        }


class SurveyRejectionForm(forms.ModelForm):
    class Meta:
        model = Survey

        fields = (
            "rejection_reason",
            "notes",
        )

        widgets = {
            "rejection_reason": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Why is this survey being rejected?",
                },
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Additional reviewer comments (optional)...",
                },
            ),
        }

    def clean_rejection_reason(self):
        reason = self.cleaned_data.get(
            "rejection_reason",
            "",
        ).strip()

        if not reason:
            raise forms.ValidationError(
                "Please provide a reason for rejecting this survey."
            )

        return reason
