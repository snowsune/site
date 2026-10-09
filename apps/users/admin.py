from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path

from .forms import EmailBlastForm
from .models import CustomUser
from .utils import email_blast_recipients, send_email_blast


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    change_list_template = "admin/users/customuser/change_list.html"
    fieldsets = UserAdmin.fieldsets + (
        (
            "External/Profile Info",
            {
                "fields": (
                    "profile_picture",
                    "fa_url",
                    "flist_url",
                    "bio",
                    "discord_id",
                    "size_diff_image",
                    "badges",
                )
            },
        ),
        (
            "Email Verification",
            {
                "fields": (
                    "email_verified",
                    "email_verification_token",
                    "email_verification_sent_at",
                )
            },
        ),
    )

    list_display = ["username", "email", "is_staff", "email_verified"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "email-blast/",
                self.admin_site.admin_view(self.email_blast_view),
                name="users_customuser_email_blast",
            ),
        ]
        return custom_urls + urls

    def email_blast_view(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied

        recipients = email_blast_recipients()
        if request.method == "POST":
            form = EmailBlastForm(request.POST, recipient_count=len(recipients))
            if form.is_valid():
                if not recipients:
                    self.message_user(
                        request,
                        "Nobody to email???",
                    )
                    return redirect("admin:users_customuser_changelist")
                sent, failed = send_email_blast(
                    form.cleaned_data["subject"],
                    form.cleaned_data["body"],
                    recipients,
                )
                if failed:
                    self.message_user(
                        request,
                        f"Sent {sent}. Failed for: {', '.join(failed)}",
                        level="warning",
                    )
                else:
                    self.message_user(request, f"Sent {sent} email(s).")
                return redirect("admin:users_customuser_changelist")
        else:
            form = EmailBlastForm(recipient_count=len(recipients))

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "form": form,
            "title": "Email blast",
            "recipient_count": len(recipients),
        }
        return TemplateResponse(
            request, "admin/users/customuser/email_blast.html", context
        )
