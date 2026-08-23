"""Service layer for translation operations.

Encapsulates business logic so views stay thin. The translation flow:
1. Check Django cache for a previous translation of the same text+language
2. Check the database for any user's previous translation of the same text+language
3. Call the funtranslations API if no cached/DB result exists
4. Cache the result for future requests
"""

from django.conf import settings
from django.core.cache import cache

from .api_client import APIFunTranslation
from .models import Translation

CACHE_PREFIX = "translation"
CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours


class TranslationService:
    """Handles the translation pipeline: cache → DB → API."""

    def __init__(self, api_client=None):
        self.api_client = api_client or APIFunTranslation()

    def translate(self, text: str, language: str) -> str:
        """Translate *text* into *language*, using cache/DB when possible.

        Raises:
            ValueError: If text is empty.
            RateLimitError: If the API rate limit is exceeded.
            TranslationError: For any other API failure.
        """
        if not text or not text.strip():
            raise ValueError("Text to translate cannot be empty.")

        # 1. Check cache
        cache_key = f"{CACHE_PREFIX}:{language}:{hash(text)}"
        result = cache.get(cache_key)
        if result is not None:
            return result

        # 2. Check database (any user's previous translation)
        existing = (
            Translation.objects.filter(original_text=text, target_language=language).only("translated_text").first()
        )
        if existing is not None:
            cache.set(cache_key, existing.translated_text, CACHE_TIMEOUT)
            return existing.translated_text

        # 3. Call the API
        result = self.api_client.translate(language, text)

        # 4. Cache for future requests
        cache.set(cache_key, result, CACHE_TIMEOUT)

        return result


def get_language_label(slug: str) -> str:
    """Return the human-readable label for a language slug."""
    for _group_label, languages in settings.SCIFILINGO_LANGUAGES:
        for code, label in languages:
            if code == slug:
                return label
    return slug
