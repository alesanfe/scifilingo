from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .api_client import APIFunTranslation, RateLimitError, TranslationError
from .models import Translation


@login_required
def home(request):
    from django.conf import settings

    languages = getattr(settings, "SCIFILINGO_LANGUAGES", [])

    if request.method == "POST":
        text_to_translate = request.POST.get("text_to_translate", "").strip()
        target_language = request.POST.get("target_language", "").strip()

        if not text_to_translate:
            messages.error(request, "Please enter some text to translate.")
            return render(request, "translation/home.html", {"languages": languages})

        translator = APIFunTranslation()
        try:
            translated_text = translator.translate(target_language, text_to_translate)
        except RateLimitError as exc:
            messages.error(request, str(exc))
            return render(request, "translation/home.html", {"languages": languages})
        except TranslationError as exc:
            messages.error(request, str(exc))
            return render(request, "translation/home.html", {"languages": languages})

        translation = Translation(
            user=request.user,
            original_text=text_to_translate,
            translated_text=translated_text,
            target_language=target_language,
        )
        translation.save()

        return render(request, "translation/results.html", {"translated_text": translated_text})

    return render(request, "translation/home.html", {"languages": languages})


@login_required
def translation_history(request):
    translations = Translation.objects.filter(user=request.user)
    return render(request, "translation/history.html", {"translations": translations})


@login_required
def translation_details(request, translation_id):
    # Filter by user to prevent IDOR (users can only see their own translations)
    translation = get_object_or_404(Translation, id=translation_id, user=request.user)
    return render(request, "translation/details.html", {"translation": translation})
