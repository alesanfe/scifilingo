import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestProfileView:
    def test_profile_requires_login(self, client):
        response = client.get(reverse("profile"))
        assert response.status_code == 302

    def test_profile_shows_stats(self, auth_client, user):
        from traductor_app.models import Translation

        for i in range(3):
            Translation.objects.create(
                user=user, original_text=f"text {i}", translated_text=f"trans {i}", target_language="yoda"
            )

        response = auth_client.get(reverse("profile"))
        assert response.status_code == 200
        assert response.context["total_translations"] == 3
        assert response.context["favorite_language"] is not None
        assert response.context["favorite_language"]["slug"] == "yoda"

    def test_profile_no_translations(self, auth_client):
        response = auth_client.get(reverse("profile"))
        assert response.status_code == 200
        assert response.context["total_translations"] == 0
        assert response.context["favorite_language"] is None


@pytest.mark.django_db
class TestChangePasswordView:
    def test_change_password_requires_login(self, client):
        response = client.get(reverse("change_password"))
        assert response.status_code == 302

    def test_change_password_get(self, auth_client):
        response = auth_client.get(reverse("change_password"))
        assert response.status_code == 200
        assert "form" in response.context

    def test_change_password_post_success(self, auth_client, user):
        response = auth_client.post(
            reverse("change_password"),
            {
                "old_password": "pass1234",
                "new_password1": "newpass1234",
                "new_password2": "newpass1234",
            },
        )
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.check_password("newpass1234")

    def test_change_password_wrong_old(self, auth_client, user):
        response = auth_client.post(
            reverse("change_password"),
            {
                "old_password": "wrongpassword",
                "new_password1": "newpass1234",
                "new_password2": "newpass1234",
            },
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.check_password("pass1234")
