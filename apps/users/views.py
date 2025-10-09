from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from .models import CustomUser


# For overlapping registration!
class CustomRegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "password1", "password2"]
        labels = {
            "username": "Username:",
            "first_name": "First Name:",
            "last_name": "Last Name:",
        }
        help_texts = {
            "username": "What you login with.",
            "first_name": "Your OC name or preferred name.",
            "last_name": "Optional OC or preffered last name",
            "password1": "Choose a secure password.",
            "password2": "Repeat your password.",
        }


# Profile editing form
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["bio", "profile_picture", "fa_url", "flist_url"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4, "cols": 50}),
        }


# Registration view
def register_view(request):
    if request.method == "POST":
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")
    else:
        form = CustomRegisterForm()
    return render(request, "users/register.html", {"form": form})


# Account editing
@login_required
def edit_account_view(request):
    if request.method == "POST":
        if "disconnect_discord" in request.POST:
            # Disconnect Discord account
            request.user.discord_id = None
            request.user.discord_username = None
            request.user.discord_access_token = None
            request.user.discord_refresh_token = None
            request.user.discord_token_expires = None
            request.user.save()
            messages.success(request, "Discord account disconnected successfully.")
            return redirect("account-edit")

        elif "save_profile" in request.POST:
            # Save profile changes
            form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect("account-edit")
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            form = ProfileEditForm(instance=request.user)
    else:
        form = ProfileEditForm(instance=request.user)

    context = {
        "user": request.user,
        "has_discord": bool(request.user.discord_access_token),
        "form": form,
    }
    return render(request, "users/edit.html", context)


# User Gallery!
def user_gallery(request):
    verified_users = CustomUser.objects.filter(is_verified=True)
    return render(request, "users/gallery.html", {"users": verified_users})
