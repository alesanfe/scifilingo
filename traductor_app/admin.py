"""Admin configuration for the translation app."""

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from traductor_app.models import Translation


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    """Admin configuration for the Translation model.

    Uses Django 5.2 features: show_facets, search_help_text, list_select_related.
    """

    list_display = (
        "id",
        "user",
        "target_language",
        "original_text_preview",
        "translated_text_preview",
        "translation_date",
    )
    list_display_links = ("id", "user")
    list_filter = ("target_language", "translation_date", "user__is_staff")
    search_fields = ("original_text", "translated_text", "user__username")
    search_help_text = _("Search by original text, translated text, or username.")
    date_hierarchy = "translation_date"
    ordering = ("-translation_date",)
    list_select_related = ("user",)
    list_per_page = 25
    show_facets = True  # type: ignore[assignment]  # ShowFacets enum, True is valid
    readonly_fields = ("translation_date", "formatted_original", "formatted_translated")
    raw_id_fields = ("user",)
    autocomplete_fields = ("user",)
    actions = ("bulk_delete_selected",)

    fieldsets = (
        (None, {"fields": ("user", "target_language", "translation_date")}),
        (_("Original Text"), {"fields": ("formatted_original", "original_text")}),
        (_("Translated Text"), {"fields": ("formatted_translated", "translated_text")}),
    )

    @admin.display(description=_("Original"), ordering="original_text")
    def original_text_preview(self, obj):
        """Show a truncated preview of the original text in the list view."""
        text = obj.original_text
        return f"{text[:60]}..." if len(text) > 60 else text

    @admin.display(description=_("Translated"), ordering="translated_text")
    def translated_text_preview(self, obj):
        """Show a truncated preview of the translated text in the list view."""
        text = obj.translated_text
        return f"{text[:60]}..." if len(text) > 60 else text

    @admin.display(description=_("Original Text (formatted)"))
    def formatted_original(self, obj):
        """Render the original text in a styled box."""
        return format_html(
            '<div style="background:#1a1f2e;border:1px solid #2a3142;border-radius:8px;'
            'padding:12px;font-family:monospace;white-space:pre-wrap;word-wrap:break-word;">{}</div>',
            obj.original_text,
        )

    @admin.display(description=_("Translated Text (formatted)"))
    def formatted_translated(self, obj):
        """Render the translated text in a styled box with accent color."""
        return format_html(
            '<div style="background:#0d1117;border:1px solid #00d9ff;border-radius:8px;'
            "padding:12px;font-family:monospace;white-space:pre-wrap;word-wrap:break-word;"
            'color:#00d9ff;">{}</div>',
            obj.translated_text,
        )

    def get_queryset(self, request):
        """Optimize queryset with prefetch for performance."""
        return super().get_queryset(request).select_related("user")

    @admin.action(description=_("Delete selected translations (with confirmation)"))
    def bulk_delete_selected(self, request, queryset):
        """Bulk delete action with count display."""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, _(f"{count} translation(s) deleted."))


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    """Admin for viewing the admin action log (read-only audit trail)."""

    list_display = ("action_time", "user", "action_flag", "change_message", "content_type", "object_id")
    list_filter = ("action_flag", "content_type", "action_time")
    search_fields = ("change_message", "user__username", "object_repr")
    search_help_text = _("Search by change message, username, or object representation.")
    date_hierarchy = "action_time"
    ordering = ("-action_time",)
    list_select_related = ("user", "content_type")
    list_per_page = 50
    readonly_fields = (
        "action_time",
        "user",
        "content_type",
        "object_id",
        "object_repr",
        "action_flag",
        "change_message",
    )
    show_facets = True  # type: ignore[assignment]  # ShowFacets enum, True is valid

    def has_add_permission(self, request):
        """Log entries are created automatically, not manually."""
        return False

    def has_change_permission(self, request, obj=None):
        """Log entries are immutable (audit trail)."""
        return False
