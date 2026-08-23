"""URL patterns for the user management app (auth, profile, language)."""

from django.urls import path

from user_management.views import (
    change_password_view,
    login_view,
    logout_view,
    profile_view,
    set_language_view,
    signin_view,
)

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("signin/", signin_view, name="signin"),
    path("profile/", profile_view, name="profile"),
    path("change-password/", change_password_view, name="change_password"),
    path("set-language/<str:lang_code>/", set_language_view, name="set_language"),
]
