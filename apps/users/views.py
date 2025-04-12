from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
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


# Account editing (placeholder for now)
@login_required
def edit_account_view(request):
    return render(request, "users/edit.html")


# User Gallery!
def user_gallery(request):
    verified_users = CustomUser.objects.filter(is_verified=True)
    return render(request, "users/gallery.html", {"users": verified_users})
