from traductor_app.forms import TranslationForm


class TestTranslationForm:
    def test_valid_data(self):
        form = TranslationForm(data={"text_to_translate": "Hello", "target_language": "yoda"})
        assert form.is_valid()

    def test_empty_text_invalid(self):
        form = TranslationForm(data={"text_to_translate": "", "target_language": "yoda"})
        assert not form.is_valid()
        assert "text_to_translate" in form.errors

    def test_text_over_max_length_invalid(self):
        form = TranslationForm(data={"text_to_translate": "x" * 1001, "target_language": "yoda"})
        assert not form.is_valid()
        assert "text_to_translate" in form.errors

    def test_invalid_language_invalid(self):
        form = TranslationForm(data={"text_to_translate": "Hello", "target_language": "nonexistent"})
        assert not form.is_valid()
        assert "target_language" in form.errors

    def test_form_has_language_choices(self):
        form = TranslationForm()
        choices = form.fields["target_language"].choices
        assert len(choices) > 0
        assert ("yoda", "Yoda") in choices
