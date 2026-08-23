from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView
from django_ratelimit.decorators import ratelimit

from .forms import TranslationForm
from .models import Translation
from .services import TranslationService, get_language_label


@ratelimit(key="user", rate="10/m", method="POST", block=False)
@login_required
def home(request: HttpRequest) -> HttpResponse:
    form = TranslationForm()

    if request.method == "POST":
        # Check rate limit
        if getattr(request, "limited", False):
            error_msg = "You're translating too fast. Please wait a moment and try again."
            if request.headers.get("HX-Request"):
                return render(
                    request,
                    "translation/partials/error.html",
                    {"error_message": error_msg},
                )
            messages.error(request, error_msg)
            return render(request, "translation/home.html", {"form": TranslationForm()})

        form = TranslationForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data["text_to_translate"]
            language = form.cleaned_data["target_language"]

            service = TranslationService()
            try:
                translated_text = service.translate(text, language)
            except Exception as exc:
                error_msg = str(exc)
                if request.headers.get("HX-Request"):
                    return render(
                        request,
                        "translation/partials/error.html",
                        {"error_message": error_msg},
                    )
                messages.error(request, error_msg)
                return render(request, "translation/home.html", {"form": form})

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
            if request.headers.get("HX-Request"):
                return render(request, "translation/partials/result.html", context)
            return render(request, "translation/results.html", context)

        if request.headers.get("HX-Request"):
            errors = "; ".join(f"{f.label}: {', '.join(f.errors)}" for f in form if f.errors)
            return render(
                request,
                "translation/partials/error.html",
                {"error_message": errors or "Please correct the errors below."},
            )

    return render(request, "translation/home.html", {"form": form})


class TranslationHistoryView(LoginRequiredMixin, ListView):
    model = Translation
    template_name = "translation/history.html"
    paginate_by = 10

    def get_queryset(self):
        qs = Translation.objects.filter(user=self.request.user)
        search = self.request.GET.get("q", "").strip()
        language = self.request.GET.get("lang", "").strip()
        if search:
            qs = qs.filter(original_text__icontains=search) | qs.filter(translated_text__icontains=search)
        if language:
            qs = qs.filter(target_language=language)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        context["selected_language"] = self.request.GET.get("lang", "")
        context["language_groups"] = self._get_language_choices()
        return context

    def _get_language_choices(self):
        from django.conf import settings

        choices = []
        for _group_label, languages in settings.SCIFILINGO_LANGUAGES:
            for slug, label in languages:
                choices.append((slug, label))
        return choices


@login_required
def translation_details(request: HttpRequest, translation_id: int) -> HttpResponse:
    translation = get_object_or_404(Translation, id=translation_id, user=request.user)
    return render(
        request,
        "translation/details.html",
        {"translation": translation, "language_label": get_language_label(translation.target_language)},
    )


@login_required
def translation_delete(request: HttpRequest, translation_id: int) -> HttpResponse:
    translation = get_object_or_404(Translation, id=translation_id, user=request.user)
    if request.method == "POST":
        translation.delete()
        if request.headers.get("HX-Request"):
            # Return empty success response — HTMX will remove the row
            return HttpResponse(status=204)
        messages.success(request, "Translation deleted.")
        return redirect("history")
    # GET — show confirmation
    return render(
        request,
        "translation/partials/delete_confirm.html",
        {"translation": translation, "language_label": get_language_label(translation.target_language)},
    )


@login_required
def export_history(request: HttpRequest) -> HttpResponse:
    """Export the user's translation history as CSV or JSON."""
    import csv
    import json

    fmt = request.GET.get("format", "csv").lower()
    translations = Translation.objects.filter(user=request.user).order_by("-translation_date")

    if fmt == "json":
        data = [
            {
                "id": t.id,
                "original_text": t.original_text,
                "translated_text": t.translated_text,
                "target_language": t.target_language,
                "language_label": get_language_label(t.target_language),
                "date": t.translation_date.isoformat(),
            }
            for t in translations
        ]
        response = HttpResponse(json.dumps(data, indent=2), content_type="application/json")
        response["Content-Disposition"] = 'attachment; filename="scifilingo_history.json"'
        return response

    # Default: CSV
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="scifilingo_history.csv"'
    writer = csv.writer(response)
    writer.writerow(["ID", "Date", "Language", "Language Label", "Original Text", "Translated Text"])
    for t in translations:
        writer.writerow(
            [
                t.id,
                t.translation_date.strftime("%Y-%m-%d %H:%M"),
                t.target_language,
                get_language_label(t.target_language),
                t.original_text,
                t.translated_text,
            ]
        )
    return response
