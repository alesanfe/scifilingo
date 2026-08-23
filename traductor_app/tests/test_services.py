from unittest.mock import MagicMock, patch

import pytest

from traductor_app.models import Translation
from traductor_app.services import TranslationService, get_language_label


@pytest.mark.django_db
class TestTranslationService:
    def test_translate_empty_text_raises_value_error(self):
        service = TranslationService()
        with pytest.raises(ValueError, match="cannot be empty"):
            service.translate("", "yoda")

    @patch("traductor_app.services.cache")
    def test_translate_cache_hit(self, mock_cache):
        mock_cache.get.return_value = "Cached result"
        mock_api = MagicMock()

        service = TranslationService(api_client=mock_api)
        result = service.translate("Hello", "yoda")

        assert result == "Cached result"
        mock_api.translate.assert_not_called()

    @patch("traductor_app.services.cache")
    def test_translate_db_hit(self, mock_cache, user):
        """When cache misses but DB has the translation, use DB result."""
        mock_cache.get.return_value = None
        mock_cache.set = MagicMock()
        Translation.objects.create(
            user=user, original_text="Hello", translated_text="DB result", target_language="yoda"
        )
        mock_api = MagicMock()

        service = TranslationService(api_client=mock_api)
        result = service.translate("Hello", "yoda")

        assert result == "DB result"
        mock_api.translate.assert_not_called()
        mock_cache.set.assert_called_once()

    @patch("traductor_app.services.cache")
    def test_translate_api_call(self, mock_cache, db):
        """When cache and DB miss, call the API and cache the result."""
        mock_cache.get.return_value = None
        mock_cache.set = MagicMock()
        mock_api = MagicMock()
        mock_api.translate.return_value = "API result"

        service = TranslationService(api_client=mock_api)
        result = service.translate("Hello", "yoda")

        assert result == "API result"
        mock_api.translate.assert_called_once_with("yoda", "Hello")
        mock_cache.set.assert_called_once()


class TestGetLanguageLabel:
    def test_known_language(self):
        assert get_language_label("yoda") == "Yoda"

    def test_unknown_language_returns_slug(self):
        assert get_language_label("unknown") == "unknown"
