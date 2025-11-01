from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from django.conf import settings
import logging
from .models import CustomUser
from .utils import send_verification_email, verify_email_token


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


def send_new_user_webhook(user):
    """New user ping!"""
    try:
        # Get webhook URL from site settings
        from snowsune.models import SiteSetting

        webhook_setting = SiteSetting.objects.filter(key="moderator_webhook").first()
        if not webhook_setting or not webhook_setting.value:
            return  # No webhook configured

        webhook_url = webhook_setting.value.strip()
        if not webhook_url:
            return

        # Import here to avoid circular imports
        from apps.commorganizer.utils import send_discord_webhook

        # Create notification message
        display_name = user.first_name or user.username
        message = f"**New User Registered!**\n\n"
        message += f"**Username:** {user.username}\n"
        if user.first_name:
            message += f"**Name:** {user.first_name}"
            if user.last_name:
                message += f" {user.last_name}"
            message += "\n"
        message += f"\n**Profile:** {settings.SITE_URL}/user/{user.username}"

        # Send webhook
        send_discord_webhook(webhook_url, message)

    except Exception as e:
        # Log error but don't break the registration process
        logging.error(
            f"Failed to send Discord webhook for new user {user.username}: {e}"
        )


# Profile editing form
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["email", "bio", "profile_picture", "fa_url", "flist_url"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4, "cols": 50}),
            "email": forms.EmailInput(attrs={"type": "email"}),
        }


# Registration view
def register_view(request):
    if request.method == "POST":
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Send webhook notification for new user
            send_new_user_webhook(user)
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

        elif "set_email_and_verify" in request.POST:
            # So, if you're just setting your email
            # the first time (from the popup box) this
            # should kinda automate the, get email, send it
            email = request.POST.get("email", "").strip()
            if not email:
                messages.error(request, "Please enter an email address.")
            else:
                request.user.email = email
                request.user.save()
                if send_verification_email(request.user):
                    messages.success(
                        request,
                        "Email set and verification sent! Please check your inbox.",
                    )
                else:
                    messages.warning(
                        request,
                        "Email set, but verification email failed to send :c You can resend it below.",
                    )
            return redirect("account-edit")

        elif "send_verification" in request.POST:
            # Send verification email
            if not request.user.email:
                messages.error(request, "Please set your email address first.")
            elif send_verification_email(request.user):
                messages.success(
                    request, "Verification email sent! Please check your inbox."
                )
            else:
                messages.error(
                    request,
                    "Failed to send verification email. Please try again later.",
                )
            return redirect("account-edit")

        elif "save_profile" in request.POST:
            # Save profile changes
            form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                # If email changed, mark as unverified
                old_email = request.user.email
                form.save()
                new_email = form.cleaned_data.get("email")
                if old_email != new_email and new_email:
                    request.user.email_verified = False
                    request.user.save()
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
    verified_users = CustomUser.objects.filter(email_verified=True).order_by(
        "-date_joined"
    )
    return render(request, "users/gallery.html", {"users": verified_users})


# User Profile Page
def user_profile(request, username):
    profile_user = get_object_or_404(CustomUser, username=username, email_verified=True)
    return render(request, "users/profile.html", {"profile_user": profile_user})


# Email verification views
def verify_email_view(request, user_id, token):
    """
    Handle email verification link clicks.
    """
    user = get_object_or_404(CustomUser, id=user_id)

    if verify_email_token(user, token):
        messages.success(request, "Email verified successfully!")
    else:
        messages.error(request, "Invalid or expired verification link.")

    return redirect("account-edit")


@login_required
def resend_verification_email_view(request):
    """
    Resend verification email to the logged-in user.
    """
    if request.user.email_verified:
        messages.info(request, "Your email is already verified.")
        return redirect("account-edit")

    if not request.user.email:
        messages.error(request, "Please set your email address first.")
        return redirect("account-edit")

    if send_verification_email(request.user):
        messages.success(request, "Verification email sent! Please check your inbox.")
    else:
        messages.error(
            request, "Failed to send verification email. Please try again later."
        )

    return redirect("account-edit")
