import pytest
from django.contrib.auth.models import User

from traductor_app.models import Translation


@pytest.mark.django_db
class TestTranslationModel:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(username="tester", password="pass1234")

    def test_translation_creation(self, user):
        t = Translation.objects.create(
            user=user,
            original_text="Hello",
            translated_text="Hola",
            target_language="yoda",
        )
        assert t.original_text == "Hello"
        assert t.target_language == "yoda"
        assert t.id is not None

    def test_translation_str(self, user):
        t = Translation.objects.create(
            user=user,
            original_text="Hi",
            translated_text="Ho",
            target_language="sith",
        )
        assert str(t) == f"Translation #{t.id} by tester"

    def test_translation_default_ordering(self, user):
        first = Translation.objects.create(
            user=user, original_text="first", translated_text="f", target_language="yoda"
        )
        second = Translation.objects.create(
            user=user, original_text="second", translated_text="s", target_language="yoda"
        )
        translations = list(Translation.objects.all())
        # Meta ordering = ['-translation_date'], so newest first
        assert translations[0] == second
        assert translations[1] == first
