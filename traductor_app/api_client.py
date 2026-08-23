from dataclasses import dataclass, field

import requests
from django.conf import settings


class TranslationError(Exception):
    """Raised when the translation API call fails."""


class RateLimitError(TranslationError):
    """Raised when the funtranslations API rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


@dataclass
class APIFunTranslation:
    """Client for the funtranslations.com translation API.

    Free tier: 60 calls/day, 5 calls/hour (no API key required).
    Paid plans: pass an API key via the FUNTRANSLATIONS_API_KEY env var
    to raise the limit (1,000-12,500 calls/day).
    """

    endpoint: str = "https://api.funtranslations.com/translate/"
    api_key: str = field(default_factory=lambda: getattr(settings, "FUNTRANSLATIONS_API_KEY", ""))
    timeout: float = 10.0

    def _build_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-FunTranslations-Api-Secret"] = self.api_key
        return headers

    def translate(self, language: str, text: str) -> str:
        """Translate *text* into the fictional *language*.

        Args:
            language: Language slug accepted by funtranslations (e.g. 'yoda').
            text: The text to translate.

        Returns:
            The translated text.

        Raises:
            ValueError: If *text* is empty.
            RateLimitError: If the API rate limit is exceeded.
            TranslationError: For any other request/parse failure.
        """
        if not text or not text.strip():
            raise ValueError("Text to translate cannot be empty.")

        url = f"{self.endpoint}{language}.json"
        data = {"text": text}
        headers = self._build_headers()

        try:
            response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
        except requests.exceptions.Timeout as exc:
            raise TranslationError("The translation API timed out. Try again later.") from exc
        except requests.exceptions.RequestException as exc:
            raise TranslationError("Could not reach the translation API.") from exc

        # Rate limited
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_seconds = int(retry_after) if retry_after and retry_after.isdigit() else None
            raise RateLimitError(
                "Rate limit exceeded. The free tier allows 5 calls/hour and 60/day.",
                retry_after=retry_seconds,
            )

        if not response.ok:
            raise TranslationError(f"Translation API returned status {response.status_code}.")

        try:
            return response.json()["contents"]["translated"]
        except (ValueError, KeyError) as exc:
            raise TranslationError("Unexpected response format from the translation API.") from exc
