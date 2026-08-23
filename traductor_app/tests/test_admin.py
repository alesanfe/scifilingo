"""Tests for the custom admin configuration."""

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from traductor_app.models import Translation

User = get_user_model()


class AdminSetupTestCase(TestCase):
    """Base test case with a superuser and authenticated client."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(username="admin", email="admin@test.com", password="admin1234")
        cls.user = User.objects.create_user(username="translator", password="pass1234")

    def setUp(self):
        self.client = Client()
        self.client.login(username="admin", password="admin1234")


class AdminBrandingTest(AdminSetupTestCase):
    """Test that the admin site has SciFiLingo branding."""

    def test_admin_site_header(self):
        """The admin site header should be customized."""
        self.assertEqual(admin.site.site_header, "SciFiLingo Administration")
        self.assertEqual(admin.site.site_title, "SciFiLingo Admin")
        self.assertEqual(admin.site.index_title, "Dashboard")

    def test_admin_login_page_has_branding(self):
        """The admin login page should show SciFiLingo branding."""
        self.client.logout()
        response = self.client.get(reverse("admin:login"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SciFiLingo", response.content)


class AdminDashboardTest(AdminSetupTestCase):
    """Test the admin dashboard with stats."""

    def test_dashboard_shows_stats(self):
        """The admin index should show dashboard statistics."""
        Translation.objects.create(
            user=self.user,
            original_text="Hello",
            translated_text="Hola",
            target_language="yoda",
        )
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SciFiLingo Overview", response.content)
        self.assertIn(b"Total Users", response.content)
        self.assertIn(b"Total Translations", response.content)
        self.assertIn(b"Top Languages", response.content)
        self.assertIn(b"Top Users", response.content)

    def test_dashboard_shows_zero_stats_when_empty(self):
        """The dashboard should render even with no data."""
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Total Users", response.content)


class TranslationAdminTest(AdminSetupTestCase):
    """Test the TranslationAdmin configuration."""

    def test_translation_list_view(self):
        """The translation changelist should load with custom columns."""
        Translation.objects.create(
            user=self.user,
            original_text="Hello world",
            translated_text="Hola mundo",
            target_language="yoda",
        )
        response = self.client.get(reverse("admin:traductor_app_translation_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hello world", response.content)

    def test_translation_detail_view(self):
        """The translation change form should load with formatted fields."""
        t = Translation.objects.create(
            user=self.user,
            original_text="Test text",
            translated_text="Translated text",
            target_language="sith",
        )
        response = self.client.get(reverse("admin:traductor_app_translation_change", args=[t.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"formatted_original", response.content)
        self.assertIn(b"formatted_translated", response.content)

    def test_translation_admin_registered(self):
        """Translation should be registered with the custom admin class."""
        self.assertIn(Translation, admin.site._registry)

    def test_show_facets_enabled(self):
        """Django 5.2 show_facets should be enabled on TranslationAdmin."""
        from traductor_app.admin import TranslationAdmin

        self.assertTrue(TranslationAdmin.show_facets)

    def test_search_help_text_set(self):
        """Django 5.2 search_help_text should be set."""
        from traductor_app.admin import TranslationAdmin

        self.assertIsNotNone(TranslationAdmin.search_help_text)


class CustomUserAdminTest(AdminSetupTestCase):
    """Test the custom UserAdmin configuration."""

    def test_user_list_shows_translation_count(self):
        """The user changelist should show the translation_count column."""
        Translation.objects.create(
            user=self.user,
            original_text="Hi",
            translated_text="Hola",
            target_language="yoda",
        )
        response = self.client.get(reverse("admin:auth_user_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"translator", response.content)

    def test_user_admin_registered_custom(self):
        """User should be registered with CustomUserAdmin, not default UserAdmin."""
        from user_management.admin import CustomUserAdmin

        registered = admin.site._registry.get(User)
        self.assertIsInstance(registered, CustomUserAdmin)

    def test_user_show_facets_enabled(self):
        """Django 5.2 show_facets should be enabled on CustomUserAdmin."""
        from user_management.admin import CustomUserAdmin

        self.assertTrue(CustomUserAdmin.show_facets)


class LogEntryAdminTest(AdminSetupTestCase):
    """Test the LogEntry admin (audit trail)."""

    def test_logentry_list_view(self):
        """The log entry changelist should load."""
        # Create a log entry by performing an admin action
        Translation.objects.create(
            user=self.user,
            original_text="test",
            translated_text="test",
            target_language="yoda",
        )
        response = self.client.get(reverse("admin:admin_logentry_changelist"))
        self.assertEqual(response.status_code, 200)

    def test_logentry_read_only(self):
        """LogEntry should be read-only (no add/change permission)."""
        from traductor_app.admin import LogEntryAdmin

        self.assertFalse(LogEntryAdmin.has_add_permission(None, LogEntryAdmin))
        self.assertFalse(LogEntryAdmin.has_change_permission(None, LogEntryAdmin))

    def test_logentry_registered(self):
        """LogEntry should be registered in admin."""
        self.assertIn(LogEntry, admin.site._registry)
