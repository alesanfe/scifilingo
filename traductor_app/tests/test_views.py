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
        assert "form" in response.context

    def test_home_post_empty_text_shows_error(self, auth_client):
        response = auth_client.post(reverse("home"), {"text_to_translate": "", "target_language": "yoda"})
        assert response.status_code == 200
        form = response.context["form"]
        assert form.errors

    @patch("traductor_app.services.APIFunTranslation")
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
        assert response.context["language_label"] == "Yoda Speak"
        assert Translation.objects.filter(user=user).count() == 1

    @patch("traductor_app.services.cache")
    @patch("traductor_app.services.APIFunTranslation")
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
        mock_translator.translate.assert_not_called()

    @patch("traductor_app.services.cache")
    @patch("traductor_app.services.APIFunTranslation")
    def test_home_post_uses_db_when_not_cached(self, mock_translator_class, mock_cache, auth_client, user):
        """When cache misses, should check DB before calling API."""
        # Cache miss
        mock_cache.get.return_value = None
        mock_cache.set = MagicMock()
        mock_translator = MagicMock()
        mock_translator_class.return_value = mock_translator

        # Pre-existing translation in DB
        Translation.objects.create(
            user=user, original_text="Hello", translated_text="DB translation", target_language="yoda"
        )

        response = auth_client.post(
            reverse("home"),
            {"text_to_translate": "Hello", "target_language": "yoda"},
        )
        assert response.context["translated_text"] == "DB translation"
        # API should not be called when DB has the translation
        mock_translator.translate.assert_not_called()

    def test_home_htmx_request_returns_partial(self, auth_client):
        """HTMX requests should return the result partial, not full page."""
        with patch("traductor_app.services.APIFunTranslation") as mock_class:
            mock_translator = MagicMock()
            mock_translator.translate.return_value = "Yoda text"
            mock_class.return_value = mock_translator

            response = auth_client.post(
                reverse("home"),
                {"text_to_translate": "Hello", "target_language": "yoda"},
                HTTP_HX_REQUEST="true",
            )
            assert response.status_code == 200
            # HTMX partial should not extend base.html
            assert b"<!DOCTYPE html>" not in response.content


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

    def test_history_search_by_text(self, auth_client, user):
        """Search should filter translations by original text."""
        Translation.objects.create(user=user, original_text="hello world", translated_text="a", target_language="yoda")
        Translation.objects.create(user=user, original_text="goodbye", translated_text="b", target_language="yoda")

        response = auth_client.get(reverse("history") + "?q=hello")
        translations = list(response.context["page_obj"])
        assert len(translations) == 1
        assert translations[0].original_text == "hello world"

    def test_history_filter_by_language(self, auth_client, user):
        """Language filter should narrow results."""
        Translation.objects.create(user=user, original_text="a", translated_text="b", target_language="yoda")
        Translation.objects.create(user=user, original_text="c", translated_text="d", target_language="klingon")

        response = auth_client.get(reverse("history") + "?lang=klingon")
        translations = list(response.context["page_obj"])
        assert len(translations) == 1
        assert translations[0].target_language == "klingon"

    def test_history_search_no_results(self, auth_client, user):
        """Search with no matches should show empty state."""
        Translation.objects.create(user=user, original_text="hello", translated_text="b", target_language="yoda")

        response = auth_client.get(reverse("history") + "?q=nonexistent")
        translations = list(response.context["page_obj"])
        assert len(translations) == 0


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
            user=user, original_text="hello", translated_text="yoda hello", target_language="yoda"
        )

        response = auth_client.get(reverse("details", args=[t.id]))
        assert response.status_code == 200
        assert response.context["translation"].original_text == "hello"
        assert response.context["language_label"] == "Yoda Speak"


@pytest.mark.django_db
class TestDeleteView:
    def test_delete_requires_login(self, client, user):
        t = Translation.objects.create(user=user, original_text="a", translated_text="b", target_language="yoda")
        response = client.get(reverse("delete", args=[t.id]))
        assert response.status_code == 302

    def test_delete_get_shows_confirmation(self, auth_client, user):
        t = Translation.objects.create(user=user, original_text="a", translated_text="b", target_language="yoda")
        response = auth_client.get(reverse("delete", args=[t.id]))
        assert response.status_code == 200
        assert b"Delete Translation" in response.content

    def test_delete_post_removes_translation(self, auth_client, user):
        t = Translation.objects.create(user=user, original_text="a", translated_text="b", target_language="yoda")
        response = auth_client.post(reverse("delete", args=[t.id]))
        assert response.status_code == 302
        assert not Translation.objects.filter(id=t.id).exists()

    def test_delete_htmx_returns_204(self, auth_client, user):
        t = Translation.objects.create(user=user, original_text="a", translated_text="b", target_language="yoda")
        response = auth_client.post(reverse("delete", args=[t.id]), HTTP_HX_REQUEST="true")
        assert response.status_code == 204
        assert not Translation.objects.filter(id=t.id).exists()

    def test_delete_idor_prevented(self, auth_client, other_user):
        """Cannot delete another user's translation."""
        t = Translation.objects.create(
            user=other_user, original_text="secret", translated_text="x", target_language="yoda"
        )
        response = auth_client.post(reverse("delete", args=[t.id]))
        assert response.status_code == 404
        assert Translation.objects.filter(id=t.id).exists()


@pytest.mark.django_db
class TestRootRedirect:
    def test_root_redirects_to_translation(self, client):
        response = client.get("/")
        assert response.status_code == 302
        assert response.url == "/translation/"
