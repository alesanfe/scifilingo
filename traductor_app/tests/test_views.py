from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from traductor_app.models import Translation


@pytest.mark.django_db
class TestHomeView:
    def test_home_requires_login(self, client):
        response = client.get(reverse("home"))
        assert response.status_code == 302
        assert "/login" in response.url

    def test_home_authenticated_get(self, client):
        user = User.objects.create_user(username="testuser", password="pass1234")
        client.force_login(user)
        response = client.get(reverse("home"))
        assert response.status_code == 200
        assert "languages" in response.context

    def test_home_post_empty_text_shows_error(self, client):
        user = User.objects.create_user(username="testuser", password="pass1234")
        client.force_login(user)
        response = client.post(reverse("home"), {"text_to_translate": "", "target_language": "yoda"})
        assert response.status_code == 200
        messages = list(response.wsgi_request._messages)
        assert any("enter some text" in str(m) for m in messages)

    @patch("traductor_app.views.APIFunTranslation")
    def test_home_post_success(self, mock_translator_class, client):
        mock_translator = MagicMock()
        mock_translator.translate.return_value = "Yoda speak this is"
        mock_translator_class.return_value = mock_translator

        user = User.objects.create_user(username="testuser", password="pass1234")
        client.force_login(user)
        response = client.post(
            reverse("home"),
            {
                "text_to_translate": "This is Yoda speak",
                "target_language": "yoda",
            },
        )
        assert response.status_code == 200
        assert response.context["translated_text"] == "Yoda speak this is"
        assert Translation.objects.filter(user=user).count() == 1


@pytest.mark.django_db
class TestHistoryView:
    def test_history_requires_login(self, client):
        response = client.get(reverse("history"))
        assert response.status_code == 302

    def test_history_shows_only_user_translations(self, client):
        user1 = User.objects.create_user(username="user1", password="pass1234")
        user2 = User.objects.create_user(username="user2", password="pass1234")
        Translation.objects.create(user=user1, original_text="a", translated_text="b", target_language="yoda")
        Translation.objects.create(user=user2, original_text="c", translated_text="d", target_language="sith")

        client.force_login(user1)
        response = client.get(reverse("history"))
        assert response.status_code == 200
        translations = list(response.context["translations"])
        assert len(translations) == 1
        assert translations[0].user == user1


@pytest.mark.django_db
class TestDetailsView:
    def test_details_requires_login(self, client):
        user = User.objects.create_user(username="user1", password="pass1234")
        t = Translation.objects.create(user=user, original_text="a", translated_text="b", target_language="yoda")
        response = client.get(reverse("details", args=[t.id]))
        assert response.status_code == 302

    def test_details_idor_prevented(self, client):
        """User cannot see another user's translation details."""
        user1 = User.objects.create_user(username="user1", password="pass1234")
        user2 = User.objects.create_user(username="user2", password="pass1234")
        t = Translation.objects.create(user=user2, original_text="secret", translated_text="x", target_language="yoda")

        client.force_login(user1)
        response = client.get(reverse("details", args=[t.id]))
        assert response.status_code == 404

    def test_details_own_translation(self, client):
        user = User.objects.create_user(username="user1", password="pass1234")
        t = Translation.objects.create(
            user=user, original_text="hello", translated_text="yoda hello", target_language="yoda"
        )

        client.force_login(user)
        response = client.get(reverse("details", args=[t.id]))
        assert response.status_code == 200
        assert response.context["translation"].original_text == "hello"
