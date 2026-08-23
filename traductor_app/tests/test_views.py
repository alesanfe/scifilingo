from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse

from traductor_app.models import Translation


@pytest.mark.django_db
class TestHomeView:
    def test_home_requires_login(self, client):
        response = client.get(reverse("home"))
        assert response.status_code == 302
        assert "/login" in response.url

    def test_home_authenticated_get(self, auth_client):
        response = auth_client.get(reverse("home"))
        assert response.status_code == 200
        assert "languages" in response.context

    def test_home_post_empty_text_shows_error(self, auth_client):
        response = auth_client.post(reverse("home"), {"text_to_translate": "", "target_language": "yoda"})
        assert response.status_code == 200
        messages = list(response.wsgi_request._messages)
        assert any("enter some text" in str(m) for m in messages)

    @patch("traductor_app.views.APIFunTranslation")
    def test_home_post_success(self, mock_translator_class, auth_client, user):
        mock_translator = MagicMock()
        mock_translator.translate.return_value = "Yoda speak this is"
        mock_translator_class.return_value = mock_translator

        response = auth_client.post(
            reverse("home"),
            {"text_to_translate": "This is Yoda speak", "target_language": "yoda"},
        )
        assert response.status_code == 200
        assert response.context["translated_text"] == "Yoda speak this is"
        assert response.context["language_label"] == "Yoda"
        assert Translation.objects.filter(user=user).count() == 1

    @patch("traductor_app.views.cache")
    @patch("traductor_app.views.APIFunTranslation")
    def test_home_post_uses_cache(self, mock_translator_class, mock_cache, auth_client):
        """Translation should be fetched from cache if available (no API call)."""
        mock_cache.get.return_value = "Cached translation"
        mock_translator = MagicMock()
        mock_translator_class.return_value = mock_translator

        response = auth_client.post(
            reverse("home"),
            {"text_to_translate": "Hello", "target_language": "yoda"},
        )
        assert response.context["translated_text"] == "Cached translation"
        # API should not be called when cache hits
        mock_translator.translate.assert_not_called()


@pytest.mark.django_db
class TestHistoryView:
    def test_history_requires_login(self, client):
        response = client.get(reverse("history"))
        assert response.status_code == 302

    def test_history_shows_only_user_translations(self, auth_client, user, other_user):
        Translation.objects.create(user=user, original_text="a", translated_text="b", target_language="yoda")
        Translation.objects.create(user=other_user, original_text="c", translated_text="d", target_language="sith")

        response = auth_client.get(reverse("history"))
        assert response.status_code == 200
        translations = list(response.context["page_obj"])
        assert len(translations) == 1
        assert translations[0].user == user

    def test_history_pagination(self, auth_client, user):
        """History should paginate at 10 items per page."""
        for i in range(12):
            Translation.objects.create(
                user=user,
                original_text=f"text {i}",
                translated_text=f"trans {i}",
                target_language="yoda",
            )

        response = auth_client.get(reverse("history"))
        assert response.context["page_obj"].number == 1
        assert response.context["page_obj"].paginator.num_pages == 2
        assert len(response.context["page_obj"]) == 10

        response = auth_client.get(reverse("history") + "?page=2")
        assert response.context["page_obj"].number == 2
        assert len(response.context["page_obj"]) == 2


@pytest.mark.django_db
class TestDetailsView:
    def test_details_requires_login(self, client, user):
        t = Translation.objects.create(user=user, original_text="a", translated_text="b", target_language="yoda")
        response = client.get(reverse("details", args=[t.id]))
        assert response.status_code == 302

    def test_details_idor_prevented(self, auth_client, other_user):
        """User cannot see another user's translation details."""
        t = Translation.objects.create(
            user=other_user, original_text="secret", translated_text="x", target_language="yoda"
        )

        response = auth_client.get(reverse("details", args=[t.id]))
        assert response.status_code == 404

    def test_details_own_translation(self, auth_client, user):
        t = Translation.objects.create(
            user=user,
            original_text="hello",
            translated_text="yoda hello",
            target_language="yoda",
        )

        response = auth_client.get(reverse("details", args=[t.id]))
        assert response.status_code == 200
        assert response.context["translation"].original_text == "hello"
        assert response.context["language_label"] == "Yoda"


@pytest.mark.django_db
class TestRootRedirect:
    def test_root_redirects_to_translation(self, client):
        response = client.get("/")
        assert response.status_code == 302
        assert response.url == "/translation/"
