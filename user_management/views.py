from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from traductor_app.models import Translation


def login_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("home")
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, "registration/login.html", {"form": form})


@login_required
def logout_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        logout(request)
        return redirect("home")
    return render(request, "registration/logout.html")


def signin_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
        messages.error(request, "Please correct the errors below.")
    else:
        form = UserCreationForm()
    return render(request, "registration/signin.html", {"form": form})


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """Show user profile with translation statistics."""
    user_translations = Translation.objects.filter(user=request.user)
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
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Keep the user logged in after password change
            from django.contrib.auth import update_session_auth_hash

            update_session_auth_hash(request, request.user)
            messages.success(request, "Your password has been changed successfully.")
            return redirect("profile")
        messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, "registration/change_password.html", {"form": form})
