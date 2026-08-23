"""Client for the funtranslations.com translation API.

Uses the web Livewire endpoint (funtranslations.com) which is not blocked
by Cloudflare, unlike the REST API endpoint (api.funtranslations.com).

The flow:
1. GET the translator page to obtain CSRF token + Livewire snapshot
2. POST to the Livewire update endpoint with the text to translate
3. Parse the response to extract the translated text
"""

import json
import re
from dataclasses import dataclass, field
from urllib.parse import unquote

import requests
from django.conf import settings
from django.core.cache import cache


class TranslationError(Exception):
    """Raised when the translation API call fails."""


class RateLimitError(TranslationError):
    """Raised when the funtranslations API rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


# Map our language slugs to funtranslations page slugs
LANGUAGE_SLUG_MAP = {
    # Tolkien
    "quenya": "quenya",
    "sindarin": "sindarin",
    "black-speech": "black-speech",
    # Star Wars
    "yoda": "yodish",
    "sith": "star-wars-sith-language",
    "huttese": "star-wars-huttese-language",
    "mando-a": "star-wars-mandalorian-language",
    "shyriiwook": "shyriiwook",
    "r2d2": "r2d2",
    "ewokese": "ewokese",
    "jawaese": "jawaese",
    "gungan": "star-wars-gungan-language",
    "cheunh": "star-wars-cheunh-language",
    "aqualish": "star-wars-aqualish-language",
    # Star Trek
    "klingon": "klingon",
    "vulcan": "vulcan",
    "romulan": "romulan",
    "cardassian": "cardassian-kardasi",
    "tamarian": "tamarian",
    # Game of Thrones
    "dothraki": "dothraki",
    "valyrian": "valyrian",
    "asshai": "asshai",
    "skroth": "skroth",
    "lhazareen": "lhazareen",
    # Elder Scrolls
    "dovahzul": "dovahzul",
    "daedric": "daedric-language",
    "aldmeris": "aldmeris",
    "ayleidoon": "ayleidoon",
    "tamrielic": "tamrielic",
    # D&D
    "elvish": "elvish",
    "orcish": "orcish",
    "draconic": "draconic",
    "halfling": "halfling",
    "goblin": "goblin-runes",
    # Warcraft
    "darnassian": "darnassian",
    "tel-quessir": "tel-quessir",
    # Harry Potter
    "parseltongue": "parseltongue",
    "gobbledegook": "gobbledegook",
    "mermish": "mermish",
    # Other
    "kryptonian": "kryptonian",
    "navi": "navi",
    "groot": "groot",
    "wakandan": "wakandan-language",
    "hylian": "hylian-alphabet",
    "simlish": "simlish",
    "rlyehian": "rlyehian",
    "old-tongue": "wheel-of-time-old-tongue",
    "predator": "predator-yautja",
    "protoss": "starcraft-protoss-khalani",
    # Fun & Silly
    "pirate": "pirate-speak",
    "minion": "minions-speak",
    "ferb-latin": "ferb-latin",
    "valspeak": "valspeak",
    "lolcat": "lolcat-speak",
    "chef": "chef-speak",
}


@dataclass
class APIFunTranslation:
    """Client for funtranslations.com via the Livewire web endpoint.

    This bypasses the Cloudflare-blocked api.funtranslations.com by using
    the same Livewire endpoint that the website's JavaScript uses.
    """

    base_url: str = "https://funtranslations.com"
    timeout: float = 15.0
    api_key: str = field(default_factory=lambda: getattr(settings, "FUNTRANSLATIONS_API_KEY", ""))
    _session: requests.Session | None = None
    _csrf: str = ""
    _xsrf: str = ""

    def _get_session(self) -> requests.Session:
        """Lazily create a session with browser-like headers."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(
                {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept-Language": "en-US,en;q=0.9",
                }
            )
        return self._session

    def _get_page(self, language_slug: str) -> str:
        """GET the translator page to extract CSRF token and Livewire snapshot.

        The snapshot + CSRF + endpoint are cached per language for 5 minutes
        to avoid an extra GET request on every translation.

        Returns the raw snapshot string for the translator-converter component.
        """
        cache_key = f"ft_livewire:{language_slug}"
        cached = cache.get(cache_key)
        if cached:
            self._csrf = cached["csrf"]
            self._xsrf = cached["xsrf"]
            self._update_url = cached["update_url"]
            return cached["snapshot"]

        session = self._get_session()
        url = f"{self.base_url}/translate/{language_slug}"

        try:
            response = session.get(url, timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            raise TranslationError("Could not reach funtranslations.com.") from exc

        if not response.ok:
            if response.status_code == 429:
                raise RateLimitError("Rate limit exceeded. Please try again later.")
            raise TranslationError(f"Failed to load translator page (status {response.status_code}).")

        # Extract CSRF token from data-csrf attribute
        csrf_match = re.search(r'data-csrf="([^"]+)"', response.text)
        if not csrf_match:
            raise TranslationError("Could not find CSRF token on translator page.")
        self._csrf = csrf_match.group(1)
        self._xsrf = unquote(session.cookies.get("XSRF-TOKEN", ""))

        # Extract the Livewire update endpoint
        uri_match = re.search(r'data-update-uri="([^"]+)"', response.text)
        if not uri_match:
            raise TranslationError("Could not find Livewire update endpoint.")
        self._update_url = uri_match.group(1)

        # Extract the translator-converter snapshot (as raw string)
        snapshots = re.findall(r'wire:snapshot="([^"]+)"', response.text)
        for snap_encoded in snapshots:
            decoded = snap_encoded.replace("&quot;", '"').replace("&amp;", "&").replace("&#039;", "'")
            try:
                snap = json.loads(decoded)
                if snap.get("memo", {}).get("name") == "translator-converter":
                    # Cache for 5 minutes — snapshot structure rarely changes
                    cache.set(
                        cache_key,
                        {
                            "snapshot": decoded,
                            "csrf": self._csrf,
                            "xsrf": self._xsrf,
                            "update_url": self._update_url,
                        },
                        timeout=300,
                    )
                    return decoded  # Return as string
            except json.JSONDecodeError:
                continue

        raise TranslationError("Could not find translator component on page.")

    def translate(self, language: str, text: str) -> str:
        """Translate *text* into the fictional *language*.

        Args:
            language: Language slug (e.g. 'yoda', 'sith').
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

        # Map our slug to funtranslations page slug
        page_slug = LANGUAGE_SLUG_MAP.get(language, language)

        # 1. GET the page to get CSRF + snapshot
        snapshot_str = self._get_page(page_slug)

        # 2. POST to the Livewire update endpoint
        session = self._get_session()
        body = {
            "_token": self._csrf,
            "components": [
                {
                    "snapshot": snapshot_str,
                    "updates": {"inputText": text},
                    "calls": [{"method": "translate", "params": []}],
                }
            ],
        }

        try:
            response = session.post(
                self._update_url,
                json=body,
                headers={
                    "X-XSRF-TOKEN": self._xsrf,
                    "X-CSRF-TOKEN": self._csrf,
                    "X-Livewire": "true",
                    "Accept": "application/json, text/plain, */*",
                    "Origin": self.base_url,
                    "Referer": f"{self.base_url}/translate/{page_slug}",
                },
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout as exc:
            raise TranslationError("The translation request timed out. Try again later.") from exc
        except requests.exceptions.RequestException as exc:
            raise TranslationError("Could not reach the translation service.") from exc

        # Rate limited
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_seconds = int(retry_after) if retry_after and retry_after.isdigit() else None
            raise RateLimitError(
                "Rate limit exceeded. The free tier allows limited calls per hour.",
                retry_after=retry_seconds,
            )

        if response.status_code == 403:
            raise TranslationError(
                "The translation service blocked this request (403). This may be temporary — try again in a moment."
            )

        if not response.ok:
            raise TranslationError(f"Translation service returned status {response.status_code}.")

        # 3. Parse the Livewire response to extract the translated text
        try:
            data = response.json()
            components = data.get("components", [])
            if not components:
                raise TranslationError("Empty response from translation service.")

            # The snapshot in the response contains the updated outputText
            snapshot_response = components[0].get("snapshot", "")
            if isinstance(snapshot_response, str):
                snap = json.loads(snapshot_response)
            else:
                snap = snapshot_response

            output = snap.get("data", {}).get("outputText", "")
            if not output:
                raise TranslationError("No translation was returned.")

            return output
        except (ValueError, KeyError, IndexError) as exc:
            raise TranslationError("Unexpected response format from the translation service.") from exc
