import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from traductor_app.api_client import APIFunTranslation, RateLimitError, TranslationError

SAMPLE_SNAPSHOT = json.dumps(
    {
        "data": {
            "translator": [None, {"class": "App\\Models\\Translator", "key": 3, "s": "mdl"}],
            "showads": True,
            "isReverse": False,
            "supportsReverse": False,
            "inputText": "",
            "outputText": "",
            "allowedLength": 1024,
        },
        "memo": {
            "id": "test123",
            "name": "translator-converter",
            "path": "translate/yodish",
            "method": "GET",
            "release": "a-a-a",
            "children": [],
            "scripts": [],
            "assets": [],
            "errors": [],
            "locale": "en",
            "islands": [],
        },
        "checksum": "abc123",
    }
)

SAMPLE_RESPONSE_SNAPSHOT = json.dumps(
    {
        "data": {
            "inputText": "Hello world",
            "outputText": "Hello world! Hmm..",
        },
        "memo": {"id": "test123", "name": "translator-converter"},
        "checksum": "abc123",
    }
)


def make_mock_page(snapshot=SAMPLE_SNAPSHOT, csrf="testcsrf"):
    """Build mock HTML for the translator page."""
    snapshot_encoded = snapshot.replace('"', "&quot;")
    return (
        f'<script data-csrf="{csrf}" '
        f'data-update-uri="https://funtranslations.com/livewire-test/update">'
        f'wire:snapshot="{snapshot_encoded}"</script>'
    )


def setup_mock_session(mock_session_class, get_response=None, post_response=None):
    """Create a mock session with GET and POST responses."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session
    mock_session.cookies = {"XSRF-TOKEN": "testxsrf"}

    if get_response is not None:
        mock_session.get.return_value = get_response
    if post_response is not None:
        mock_session.post.return_value = post_response

    return mock_session


def make_get_response(text=None, status=200):
    """Create a mock GET response."""
    r = MagicMock()
    r.ok = status < 400
    r.status_code = status
    r.text = text or make_mock_page()
    return r


def make_post_response(json_data=None, status=200, headers=None):
    """Create a mock POST response."""
    r = MagicMock()
    r.ok = status < 400
    r.status_code = status
    r.headers = headers or {}
    if json_data is not None:
        r.json.return_value = json_data
    return r


class TestAPIFunTranslation:
    def test_translate_empty_text_raises_value_error(self):
        client = APIFunTranslation()
        with pytest.raises(ValueError, match="cannot be empty"):
            client.translate("yoda", "")

    def test_translate_whitespace_only_raises_value_error(self):
        client = APIFunTranslation()
        with pytest.raises(ValueError, match="cannot be empty"):
            client.translate("yoda", "   ")

    @patch("traductor_app.api_client.requests.Session")
    def test_translate_success(self, mock_session_class):
        """Full flow: GET page → POST Livewire → extract outputText."""
        get_resp = make_get_response()
        post_resp = make_post_response(
            json_data={"components": [{"snapshot": SAMPLE_RESPONSE_SNAPSHOT, "effects": {"returns": [None]}}]}
        )
        setup_mock_session(mock_session_class, get_resp, post_resp)

        client = APIFunTranslation()
        result = client.translate("yoda", "Hello world")
        assert result == "Hello world! Hmm.."

    @patch("traductor_app.api_client.requests.Session")
    def test_translate_rate_limit_429(self, mock_session_class):
        get_resp = make_get_response()
        post_resp = make_post_response(status=429, headers={"Retry-After": "3600"})
        setup_mock_session(mock_session_class, get_resp, post_resp)

        client = APIFunTranslation()
        with pytest.raises(RateLimitError) as exc_info:
            client.translate("yoda", "Hello")
        assert exc_info.value.retry_after == 3600

    @patch("traductor_app.api_client.requests.Session")
    def test_translate_server_error(self, mock_session_class):
        get_resp = make_get_response()
        post_resp = make_post_response(status=500)
        setup_mock_session(mock_session_class, get_resp, post_resp)

        client = APIFunTranslation()
        with pytest.raises(TranslationError, match="status 500"):
            client.translate("yoda", "Hello")

    @patch("traductor_app.api_client.requests.Session")
    def test_translate_malformed_response(self, mock_session_class):
        get_resp = make_get_response()
        post_resp = make_post_response(json_data={"unexpected": "format"})
        setup_mock_session(mock_session_class, get_resp, post_resp)

        client = APIFunTranslation()
        with pytest.raises(TranslationError, match="Empty response"):
            client.translate("yoda", "Hello")

    @patch("traductor_app.api_client.requests.Session")
    def test_translate_timeout(self, mock_session_class):
        get_resp = make_get_response()
        mock_session = setup_mock_session(mock_session_class, get_resp)
        mock_session.post.side_effect = requests.exceptions.Timeout()

        client = APIFunTranslation()
        with pytest.raises(TranslationError, match="timed out"):
            client.translate("yoda", "Hello")

    @patch("traductor_app.api_client.requests.Session")
    def test_translate_no_csrf_token(self, mock_session_class):
        """Should raise TranslationError if CSRF token not found on page."""
        get_resp = make_get_response(text="<html><body>No CSRF here</body></html>")
        setup_mock_session(mock_session_class, get_resp)

        client = APIFunTranslation()
        with pytest.raises(TranslationError, match="CSRF"):
            client.translate("yoda", "Hello")

    @patch("traductor_app.api_client.requests.Session")
    def test_translate_no_snapshot(self, mock_session_class):
        """Should raise TranslationError if translator component not found."""
        get_resp = make_get_response(
            text='<script data-csrf="testcsrf" data-update-uri="https://example.com/update"></script>'
        )
        setup_mock_session(mock_session_class, get_resp)

        client = APIFunTranslation()
        with pytest.raises(TranslationError, match="translator component"):
            client.translate("yoda", "Hello")

    def test_language_slug_mapping(self):
        """Yoda slug should map to yodish page."""
        from traductor_app.api_client import LANGUAGE_SLUG_MAP

        assert LANGUAGE_SLUG_MAP["yoda"] == "yodish"
        assert LANGUAGE_SLUG_MAP["pirate"] == "pirate-speak"
