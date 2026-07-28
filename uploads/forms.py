from django import forms


class SurveyFileUploadForm(forms.Form):
    archive = forms.FileField(
        label="Survey Deliverables",
        help_text=("Upload the exported survey folder as a ZIP archive."),
        widget=forms.ClearableFileInput(
            attrs={
                "accept": ".zip",
            }
        ),
    )

    def clean_archive(self):

        archive = self.cleaned_data["archive"]

        if not archive.name.lower().endswith(".zip"):
            raise forms.ValidationError("Please upload a ZIP archive.")

        return archive
