from unittest.mock import MagicMock, patch

import pytest

from traductor_app.api_client import APIFunTranslation, RateLimitError, TranslationError


class TestAPIFunTranslation:
    def test_translate_empty_text_raises_value_error(self):
        client = APIFunTranslation()
        with pytest.raises(ValueError, match="cannot be empty"):
            client.translate("yoda", "")

    def test_translate_whitespace_only_raises_value_error(self):
        client = APIFunTranslation()
        with pytest.raises(ValueError, match="cannot be empty"):
            client.translate("yoda", "   ")

    @patch("traductor_app.api_client.requests.post")
    def test_translate_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "contents": {"translated": "Translated text", "text": "Hello", "translation": "yoda"}
        }
        mock_post.return_value = mock_response

        client = APIFunTranslation()
        result = client.translate("yoda", "Hello")
        assert result == "Translated text"

    @patch("traductor_app.api_client.requests.post")
    def test_translate_rate_limit_429(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "3600"}
        mock_post.return_value = mock_response

        client = APIFunTranslation()
        with pytest.raises(RateLimitError) as exc_info:
            client.translate("yoda", "Hello")
        assert exc_info.value.retry_after == 3600

    @patch("traductor_app.api_client.requests.post")
    def test_translate_server_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.headers = {}
        mock_post.return_value = mock_response

        client = APIFunTranslation()
        with pytest.raises(TranslationError, match="status 500"):
            client.translate("yoda", "Hello")

    @patch("traductor_app.api_client.requests.post")
    def test_translate_malformed_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"unexpected": "format"}
        mock_post.return_value = mock_response

        client = APIFunTranslation()
        with pytest.raises(TranslationError, match="Unexpected response"):
            client.translate("yoda", "Hello")

    @patch("traductor_app.api_client.requests.post")
    def test_translate_timeout(self, mock_post):
        import requests

        mock_post.side_effect = requests.exceptions.Timeout()

        client = APIFunTranslation()
        with pytest.raises(TranslationError, match="timed out"):
            client.translate("yoda", "Hello")

    @patch("traductor_app.api_client.requests.post")
    def test_translate_with_api_key(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"contents": {"translated": "result"}}
        mock_post.return_value = mock_response

        client = APIFunTranslation(api_key="test-key")
        client.translate("yoda", "Hello")

        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["X-FunTranslations-Api-Secret"] == "test-key"

    @patch("traductor_app.api_client.requests.post")
    def test_translate_without_api_key_no_header(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"contents": {"translated": "result"}}
        mock_post.return_value = mock_response

        client = APIFunTranslation(api_key="")
        client.translate("yoda", "Hello")

        _, kwargs = mock_post.call_args
        assert "X-FunTranslations-Api-Secret" not in kwargs["headers"]
