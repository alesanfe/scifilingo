"""Forms for the translation app."""

from django import forms
from django.conf import settings


class TranslationForm(forms.Form):
    text_to_translate = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Type your text here...",
            }
        ),
        min_length=1,
        max_length=1000,
        error_messages={"required": "Please enter some text to translate."},
    )
    target_language = forms.ChoiceField(
        widget=forms.Select(attrs={"class": "form-control"}),
        choices=[],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target_language"].choices = [(slug, label) for slug, label in settings.SCIFILINGO_LANGUAGES]
