import pytest

from traductor_app.models import Translation


@pytest.mark.django_db
class TestTranslationModel:
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
        assert str(t) == f"Translation #{t.id} by testuser"

    def test_translation_default_ordering(self, user):
        first = Translation.objects.create(
            user=user, original_text="first", translated_text="f", target_language="yoda"
        )
        second = Translation.objects.create(
            user=user, original_text="second", translated_text="s", target_language="yoda"
        )
        translations = list(Translation.objects.all())
        # Meta ordering = ["-translation_date"], so newest first
        assert translations[0] == second
        assert translations[1] == first

    def test_translation_cascade_delete(self, user):
        """Deleting a user should delete their translations."""
        t = Translation.objects.create(user=user, original_text="a", translated_text="b", target_language="yoda")
        user.delete()
        assert not Translation.objects.filter(id=t.id).exists()
