"""Admin configuration for the user management app (custom UserAdmin)."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from traductor_app.models import Translation

User = get_user_model()

# Unregister the default UserAdmin to replace it with our custom one
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom UserAdmin with translation count and Django 5.2 features."""

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "date_joined",
        "translation_count",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "groups", "date_joined")
    search_fields = ("username", "first_name", "last_name", "email")
    search_help_text = _("Search by username, name, or email.")
    show_facets = True  # type: ignore[assignment]  # ShowFacets enum, True is valid
    list_per_page = 25
    date_hierarchy = "date_joined"
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                "classes": ("collapse",),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    @admin.display(description=_("Translations"), ordering="translation_count")
    def translation_count(self, obj):
        """Show the number of translations made by this user."""
        count = Translation.objects.filter(user=obj).count()
        if count == 0:
            return format_html('<span style="color:#666;">{}</span>', 0)
        return format_html(
            '<span style="color:#00d9ff;font-weight:bold;">{}</span>',
            count,
        )

    def get_queryset(self, request):
        """Annotate queryset with translation count for sorting."""
        from django.db.models import Count

        return super().get_queryset(request).annotate(translation_count=Count("translation"))
