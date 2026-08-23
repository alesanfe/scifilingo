from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .api_client import APIFunTranslation, RateLimitError, TranslationError
from .models import Translation

# Cache key prefix for translation results
CACHE_PREFIX = "translation"
CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours


def _language_label(slug):
    """Return the human-readable label for a language slug."""
    for code, label in settings.SCIFILINGO_LANGUAGES:
        if code == slug:
            return label
    return slug


@login_required
def home(request):
    languages = settings.SCIFILINGO_LANGUAGES

    if request.method == "POST":
        text_to_translate = request.POST.get("text_to_translate", "").strip()
        target_language = request.POST.get("target_language", "").strip()

        if not text_to_translate:
            messages.error(request, "Please enter some text to translate.")
            return render(request, "translation/home.html", {"languages": languages})

        # Check cache first to avoid hitting the API rate limit
        cache_key = f"{CACHE_PREFIX}:{target_language}:{hash(text_to_translate)}"
        translated_text = cache.get(cache_key)

        if translated_text is None:
            translator = APIFunTranslation()
            try:
                translated_text = translator.translate(target_language, text_to_translate)
            except RateLimitError as exc:
                messages.error(request, str(exc))
                return render(request, "translation/home.html", {"languages": languages})
            except TranslationError as exc:
                messages.error(request, str(exc))
                return render(request, "translation/home.html", {"languages": languages})

            cache.set(cache_key, translated_text, CACHE_TIMEOUT)

        translation = Translation(
            user=request.user,
            original_text=text_to_translate,
            translated_text=translated_text,
            target_language=target_language,
        )
        translation.save()

        return render(
            request,
            "translation/results.html",
            {"translated_text": translated_text, "language_label": _language_label(target_language)},
        )

    return render(request, "translation/home.html", {"languages": languages})


@login_required
def translation_history(request):
    translations = Translation.objects.filter(user=request.user)
    paginator = Paginator(translations, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "translation/history.html", {"page_obj": page_obj})


@login_required
def translation_details(request, translation_id):
    # Filter by user to prevent IDOR (users can only see their own translations)
    translation = get_object_or_404(Translation, id=translation_id, user=request.user)
    return render(
        request,
        "translation/details.html",
        {"translation": translation, "language_label": _language_label(translation.target_language)},
    )
