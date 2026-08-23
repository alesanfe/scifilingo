"""Admin configuration for the translation app."""

from django.contrib import admin

from traductor_app.models import Translation


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    """Admin configuration for the Translation model."""

    list_display = ("id", "user", "target_language", "translation_date")
    list_filter = ("target_language", "translation_date")
    search_fields = ("original_text", "translated_text", "user__username")
    date_hierarchy = "translation_date"
