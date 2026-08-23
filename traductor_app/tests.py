from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User

from traductor_app.api_client import APIFunTranslation, TranslationError, RateLimitError
from traductor_app.models import Translation


class TranslationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass1234')

    def test_translation_creation(self):
        t = Translation.objects.create(
            user=self.user,
            original_text='Hello',
            translated_text='Hola',
            target_language='yoda',
        )
        self.assertEqual(t.original_text, 'Hello')
        self.assertEqual(t.target_language, 'yoda')
        self.assertIn('tester', str(t))

    def test_translation_str_format(self):
        t = Translation.objects.create(
            user=self.user,
            original_text='Hi',
            translated_text='Ho',
            target_language='sith',
        )
        self.assertEqual(str(t), f'Translation #{t.id} by tester')


class APIClientTest(TestCase):
    def test_translate_empty_text_raises_value_error(self):
        client = APIFunTranslation()
        with self.assertRaises(ValueError):
            client.translate('yoda', '')

    def test_translate_whitespace_only_raises_value_error(self):
        client = APIFunTranslation()
        with self.assertRaises(ValueError):
            client.translate('yoda', '   ')
