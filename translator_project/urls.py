"""URL configuration for translator_project project."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

# SciFiLingo branding for the admin site
admin.site.site_header = "SciFiLingo Administration"
admin.site.site_title = "SciFiLingo Admin"
admin.site.index_title = "Dashboard"
admin.site.site_url = "/translation/"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("translation/", include("traductor_app.urls")),
    path("accounts/", include("user_management.urls")),
    # allauth URLs (login, logout, signup, password reset, etc.)
    path("accounts/", include("allauth.urls")),
    # Redirect root URL to the translation app
    path("", RedirectView.as_view(url="/translation/", permanent=False)),
]

# Dev-only URLs (debug toolbar + browser reload)
if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns = (
        [
            path("__reload__/", include("django_browser_reload.urls")),
        ]
        + urlpatterns
        + debug_toolbar_urls()
    )
