from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView

from .forms import TranslationForm
from .models import Translation
from .services import TranslationService, get_language_label


@login_required
def home(request):
    form = TranslationForm()

    if request.method == "POST":
        form = TranslationForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data["text_to_translate"]
            language = form.cleaned_data["target_language"]

            service = TranslationService()
            try:
                translated_text = service.translate(text, language)
            except Exception as exc:
                messages.error(request, str(exc))
                # Re-render with the form and available languages
                return render(
                    request,
                    "translation/home.html",
                    {"form": form, "languages": _language_choices()},
                )

            Translation.objects.create(
                user=request.user,
                original_text=text,
                translated_text=translated_text,
                target_language=language,
            )

            context = {
                "translated_text": translated_text,
                "language_label": get_language_label(language),
                "original_text": text,
            }
            # HTMX requests get just the result partial
            if request.headers.get("HX-Request"):
                return render(request, "translation/partials/result.html", context)
            return render(request, "translation/results.html", context)

        # Form invalid — re-render with errors
        if request.headers.get("HX-Request"):
            return render(
                request,
                "translation/partials/form.html",
                {"form": form, "languages": _language_choices()},
            )

    return render(request, "translation/home.html", {"form": form, "languages": _language_choices()})


def _language_choices():
    from django.conf import settings

    return settings.SCIFILINGO_LANGUAGES


class TranslationHistoryView(LoginRequiredMixin, ListView):
    model = Translation
    template_name = "translation/history.html"
    paginate_by = 10

    def get_queryset(self):
        return Translation.objects.filter(user=self.request.user)


@login_required
def translation_details(request, translation_id):
    translation = get_object_or_404(Translation, id=translation_id, user=request.user)
    return render(
        request,
        "translation/details.html",
        {"translation": translation, "language_label": get_language_label(translation.target_language)},
    )
