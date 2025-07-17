from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Commission, Draft, Comment
from .forms import CommissionCreateForm, CommissionReturnForm
from django.urls import reverse
from django.http import HttpResponseRedirect
from django import forms

# Create your views here.


def commorganizer_landing(request):
    create_form = CommissionCreateForm()
    return_form = CommissionReturnForm()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            create_form = CommissionCreateForm(request.POST)
            if create_form.is_valid():
                name = create_form.cleaned_data["name"]
                password = create_form.cleaned_data["password"]
                commission, created = Commission.objects.get_or_create(
                    name=name, defaults={"artist_password": password}
                )
                if not created and commission.artist_password != password:
                    create_form.add_error(
                        "name",
                        "A commission with this name already exists and the password is incorrect.",
                    )
                else:
                    # If commission exists and password matches, or new commission created
                    return redirect(
                        "commorganizer-artist-dashboard",
                        commission_name=commission.name,
                    )
        elif action == "return":
            return_form = CommissionReturnForm(request.POST)
            if return_form.is_valid():
                password = return_form.cleaned_data["password"]
                try:
                    commission = Commission.objects.get(artist_password=password)
                    return redirect(
                        "commorganizer-artist-dashboard",
                        commission_name=commission.name,
                    )
                except Commission.DoesNotExist:
                    return_form.add_error(
                        "password", "No commission found with that password."
                    )

    return render(
        request,
        "commorganizer_home.html",
        {
            "create_form": create_form,
            "return_form": return_form,
        },
    )


class DraftUploadForm(forms.Form):
    image = forms.ImageField()


def artist_dashboard(request, commission_name):
    commission = Commission.objects.get(name=commission_name)
    # Comments: unresolved first, then resolved, both sorted by age
    unresolved_comments = Comment.objects.filter(
        draft__commission=commission, resolved=False
    ).order_by("created_at")
    resolved_comments = Comment.objects.filter(
        draft__commission=commission, resolved=True
    ).order_by("created_at")
    all_comments = list(unresolved_comments) + list(resolved_comments)
    # Drafts, newest first
    drafts = Draft.objects.filter(commission=commission).order_by("-created_at")
    # Share link
    share_link = request.build_absolute_uri(
        reverse("commorganizer-public-view", args=[commission.name])
    )

    # Handle draft upload (stub)
    upload_form = DraftUploadForm()
    if request.method == "POST":
        if "upload_draft" in request.POST:
            upload_form = DraftUploadForm(request.POST, request.FILES)
            if upload_form.is_valid():
                Draft.objects.create(
                    commission=commission, image=upload_form.cleaned_data["image"]
                )
                return HttpResponseRedirect(request.path)
        elif "toggle_resolve_comment" in request.POST:
            comment_id = request.POST.get("toggle_resolve_comment")
            try:
                comment = Comment.objects.get(
                    pk=comment_id, draft__commission=commission
                )
                comment.resolved = not comment.resolved
                comment.save()
                return HttpResponseRedirect(request.path)
            except Comment.DoesNotExist:
                pass

    return render(
        request,
        "commorganizer_artist_dashboard.html",
        {
            "commission_name": commission_name,
            "comments": all_comments,
            "drafts": drafts,
            "share_link": share_link,
            "upload_form": upload_form,
        },
    )


def public_commission_view(request, commission_name):
    commission = Commission.objects.get(name=commission_name)
    drafts = Draft.objects.filter(commission=commission).order_by("-created_at")
    draft_id = request.GET.get("draft")
    if draft_id:
        try:
            current_draft = drafts.get(pk=draft_id)
        except Draft.DoesNotExist:
            current_draft = drafts.first()
    else:
        current_draft = drafts.first()
    comments = (
        Comment.objects.filter(draft=current_draft).order_by("created_at")
        if current_draft
        else []
    )

    # Handle comment form POST
    if request.method == "POST" and current_draft and "add_comment" in request.POST:
        x = int(request.POST.get("x", 0))
        y = int(request.POST.get("y", 0))
        commenter_name = request.POST.get("commenter_name", "").strip()[:32]
        content = request.POST.get("content", "").strip()
        if commenter_name and content:
            Comment.objects.create(
                draft=current_draft,
                x=x,
                y=y,
                commenter_name=commenter_name,
                content=content,
            )
            # Redirect to same draft after comment
            return redirect(f"{request.path}?draft={current_draft.pk}")

    return render(
        request,
        "commorganizer_public_view.html",
        {
            "commission_name": commission_name,
            "drafts": drafts,
            "current_draft": current_draft,
            "comments": comments,
        },
    )
