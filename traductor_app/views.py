"""Views for the translation app: home, history, details, delete, export."""

from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.generic import ListView
from django_ratelimit.decorators import ratelimit

from .forms import TranslationForm
from .models import Translation
from .services import TranslationService, get_language_label


@ratelimit(key="user", rate="10/m", method="POST", block=False)
@login_required
def home(request: HttpRequest) -> HttpResponse:
    """Render the translation form and handle translation submissions.

    GET: show the form. POST: validate, call the translation service,
    and return the result (HTMX partial or full page).
    Applies rate limiting (10 translations/minute per user).
    """
    if request.method == "POST":
        return _handle_translation_post(request)
    return render(request, "translation/home.html", {"form": TranslationForm()})


def _handle_translation_post(request: HttpRequest) -> HttpResponse:
    """Process a POST translation request: rate-limit check, validation, API call."""
    if getattr(request, "limited", False):
        return _render_error(request, _("You're translating too fast. Please wait a moment and try again."))

    form = TranslationForm(request.POST)
    if not form.is_valid():
        errors = "; ".join(f"{f.label}: {', '.join(f.errors)}" for f in form if f.errors)  # type: ignore[arg-type]
        return _render_error(request, errors or _("Please correct the errors below."), form=form)

    text = form.cleaned_data["text_to_translate"]
    language = form.cleaned_data["target_language"]

    service = TranslationService()
    try:
        translated_text = service.translate(text, language)
    except Exception as exc:
        return _render_error(request, str(exc), form=form)

    Translation.objects.create(
        user=cast(User, request.user),
        original_text=text,
        translated_text=translated_text,
        target_language=language,
    )

    context = {
        "translated_text": translated_text,
        "language_label": get_language_label(language),
        "original_text": text,
    }
    template = "translation/partials/result.html" if request.headers.get("HX-Request") else "translation/results.html"
    return render(request, template, context)


def _render_error(request: HttpRequest, error_msg: str, form: TranslationForm | None = None) -> HttpResponse:
    """Render an error response (HTMX partial or full page with messages)."""
    if request.headers.get("HX-Request"):
        return render(request, "translation/partials/error.html", {"error_message": error_msg})
    messages.error(request, error_msg)
    return render(request, "translation/home.html", {"form": form or TranslationForm()})


class TranslationHistoryView(LoginRequiredMixin, ListView):
    """List view for the user's translation history with search and filter."""

    model = Translation
    template_name = "translation/history.html"
    paginate_by = 10

    def get_queryset(self):
        """Return filtered translations for the current user."""
        qs = Translation.objects.filter(user=cast(User, self.request.user))
        search = self.request.GET.get("q", "").strip()
        language = self.request.GET.get("lang", "").strip()
        if search:
            qs = qs.filter(original_text__icontains=search) | qs.filter(translated_text__icontains=search)
        if language:
            qs = qs.filter(target_language=language)
        return qs

    def get_context_data(self, **kwargs):
        """Add search and filter context to the template."""
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        context["selected_language"] = self.request.GET.get("lang", "")
        context["language_groups"] = self._get_language_choices()
        return context

    def _get_language_choices(self):
        """Return a flat list of (slug, label) tuples from the grouped settings."""
        from django.conf import settings

        choices = []
        for _group_label, languages in settings.SCIFILINGO_LANGUAGES:
            for slug, label in languages:
                choices.append((slug, label))
        return choices


@login_required
def translation_details(request: HttpRequest, translation_id: int) -> HttpResponse:
    """Show details of a specific translation owned by the current user."""
    translation = get_object_or_404(Translation, id=translation_id, user=cast(User, request.user))
    return render(
        request,
        "translation/details.html",
        {"translation": translation, "language_label": get_language_label(translation.target_language)},
    )


@login_required
def translation_delete(request: HttpRequest, translation_id: int) -> HttpResponse:
    """Delete a translation after confirmation (HTMX modal or POST redirect)."""
    translation = get_object_or_404(Translation, id=translation_id, user=cast(User, request.user))
    if request.method == "POST":
        translation.delete()
        if request.headers.get("HX-Request"):
            # Return empty success response — HTMX will remove the row
            return HttpResponse(status=204)
        messages.success(request, _("Translation deleted."))
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
    translations = Translation.objects.filter(user=cast(User, request.user)).order_by("-translation_date")

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
