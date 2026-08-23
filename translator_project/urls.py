"""URL configuration for translator_project project."""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("translation/", include("traductor_app.urls")),
    path("accounts/", include("user_management.urls")),
    # Redirect root URL to the translation app
    path("", RedirectView.as_view(url="/translation/", permanent=False)),
]
