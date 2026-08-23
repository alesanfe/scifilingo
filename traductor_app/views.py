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
        return Translation.objects.filter(user=self.request.user)


@login_required
def translation_details(request, translation_id):
    translation = get_object_or_404(Translation, id=translation_id, user=request.user)
    return render(
        request,
        "translation/details.html",
        {"translation": translation, "language_label": get_language_label(translation.target_language)},
    )
