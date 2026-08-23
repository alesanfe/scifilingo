"""Context processors for the admin dashboard."""

from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.db.models import Count

from traductor_app.models import Translation

User = get_user_model()


def admin_stats(request):
    """Provide dashboard statistics to the admin index template.

    Only adds context for admin URLs to avoid unnecessary queries elsewhere.
    """
    if not request.path.startswith("/admin/"):
        return {}
    return {
        "scifi_stats": {
            "total_users": User.objects.count(),
            "total_translations": Translation.objects.count(),
            "total_staff": User.objects.filter(is_staff=True).count(),
            "total_log_entries": LogEntry.objects.count(),
            "recent_translations": Translation.objects.select_related("user").order_by("-translation_date")[:5],
            "top_languages": (
                Translation.objects.values("target_language").annotate(count=Count("id")).order_by("-count")[:5]
            ),
            "top_users": (
                Translation.objects.values("user__username").annotate(count=Count("id")).order_by("-count")[:5]
            ),
        }
    }
