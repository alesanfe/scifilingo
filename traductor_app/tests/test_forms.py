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

    def test_form_has_optgroup_choices(self):
        """Form should have grouped choices (optgroup) by universe."""
        form = TranslationForm()
        choices = form.fields["target_language"].choices
        assert len(choices) > 0

        # Choices are (group_label, [(slug, label), ...]) tuples
        # Find yoda in one of the groups
        all_slugs = []
        for group in choices:
            group_label, group_choices = group
            assert isinstance(group_label, str)
            for slug, label in group_choices:
                all_slugs.append((slug, label))

        assert ("yoda", "Yoda Speak") in all_slugs
        assert ("klingon", "Klingon") in all_slugs
        assert ("dothraki", "Dothraki") in all_slugs

    def test_form_has_multiple_groups(self):
        """Form should have multiple universe groups."""
        form = TranslationForm()
        choices = form.fields["target_language"].choices
        group_labels = [g[0] for g in choices]
        assert len(group_labels) >= 5  # At least 5 universe groups
        assert any("Star Wars" in label for label in group_labels)
        assert any("Tolkien" in label for label in group_labels)
