"""Forms for the translation app."""

from django import forms
from django.conf import settings

TAILWIND_INPUT = (
    "w-full px-4 py-3 bg-scifi-surface border border-scifi-border rounded-xl "
    "text-white placeholder-gray-600 focus:outline-none focus:border-scifi-accent "
    "focus:ring-2 focus:ring-scifi-accent/20 transition-all"
)


class TranslationForm(forms.Form):
    """Form for submitting a translation request.

    Captures the text to translate and the target fictional language,
    organized by universe groups in the language selector.
    """

    text_to_translate = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": TAILWIND_INPUT,
                "rows": 4,
                "placeholder": "Type your text here...",
            }
        ),
        min_length=1,
        max_length=1000,
        error_messages={"required": "Please enter some text to translate."},
    )
    target_language = forms.ChoiceField(
        widget=forms.Select(attrs={"class": TAILWIND_INPUT}),
        choices=[],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Build optgroup choices from the grouped settings structure
        choices = []
        for group_label, languages in settings.SCIFILINGO_LANGUAGES:
            choices.append((group_label, [(slug, label) for slug, label in languages]))
        self.fields["target_language"].choices = choices
