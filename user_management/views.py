"""Views for user management: login, logout, signin, profile, password, language."""

from typing import cast

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import activate
from django.utils.translation import gettext as _

from traductor_app.models import Translation


def login_view(request: HttpRequest) -> HttpResponse:
    """Handle user login via username/password authentication."""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("home")
        messages.error(request, _("Invalid username or password."))
    else:
        form = AuthenticationForm()
    return render(request, "registration/login.html", {"form": form})


@login_required
def logout_view(request: HttpRequest) -> HttpResponse:
    """Handle user logout with a confirmation page."""
    if request.method == "POST":
        logout(request)
        return redirect("home")
    return render(request, "registration/logout.html")


def signin_view(request: HttpRequest) -> HttpResponse:
    """Handle new user registration (sign up)."""
    if request.method == "POST":
        form: UserCreationForm = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
        messages.error(request, _("Please correct the errors below."))
    else:
        form = UserCreationForm()
    return render(request, "registration/signin.html", {"form": form})


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """Show user profile with translation statistics."""
    user_translations = Translation.objects.filter(user=cast(User, request.user))
    total = user_translations.count()

    # Favorite language (most used)
    favorite_language = None
    if total > 0:
        from django.db.models import Count

        top = user_translations.values("target_language").annotate(count=Count("id")).order_by("-count").first()
        if top:
            from traductor_app.services import get_language_label

            favorite_language = {
                "slug": top["target_language"],
                "label": get_language_label(top["target_language"]),
                "count": top["count"],
            }

    # Recent translations (last 5)
    recent = user_translations.order_by("-translation_date")[:5]

    context = {
        "total_translations": total,
        "favorite_language": favorite_language,
        "recent_translations": recent,
    }
    return render(request, "registration/profile.html", context)


@login_required
def change_password_view(request: HttpRequest) -> HttpResponse:
    """Allow users to change their password."""
    if request.method == "POST":
        form = PasswordChangeForm(user=cast(User, request.user), data=request.POST)
        if form.is_valid():
            form.save()
            # Keep the user logged in after password change
            from django.contrib.auth import update_session_auth_hash

            update_session_auth_hash(request, cast(User, request.user))
            messages.success(request, _("Your password has been changed successfully."))
            return redirect("profile")
        messages.error(request, _("Please correct the errors below."))
    else:
        form = PasswordChangeForm(user=cast(User, request.user))
    return render(request, "registration/change_password.html", {"form": form})


def set_language_view(request: HttpRequest, lang_code: str) -> HttpResponse:
    """Set the user's language preference and redirect back."""
    from django.conf import settings

    supported = {code for code, _name in settings.LANGUAGES}
    if lang_code in supported:
        activate(lang_code)
        response = redirect(request.META.get("HTTP_REFERER", "home"))
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code, max_age=60 * 60 * 24 * 365)
        return response
    return redirect("home")
