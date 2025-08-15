from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from .models import Commission, Draft, Comment
from .forms import (
    CommissionCreateForm,
    CommissionCreateFormLoggedIn,
    CommissionReturnForm,
)
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django import forms
from .utils import send_discord_webhook
from django.db.models import Count, Q
from django.utils.dateparse import parse_datetime
from collections import defaultdict

User = get_user_model()

# Create your views here.


def commorganizer_landing(request):
    # Use different forms based on authentication status
    if request.user.is_authenticated:
        create_form = CommissionCreateFormLoggedIn()
    else:
        create_form = CommissionCreateForm()

    return_form = CommissionReturnForm()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            # Use the appropriate form based on user status
            if request.user.is_authenticated:
                create_form = CommissionCreateFormLoggedIn(request.POST)
            else:
                create_form = CommissionCreateForm(request.POST)

            if create_form.is_valid():
                name = create_form.cleaned_data["name"]

                # If user is logged in, create commission linked to them
                if request.user.is_authenticated:
                    commission, created = Commission.objects.get_or_create(
                        name=name,
                        defaults={"user": request.user, "artist_password": None},
                    )
                    if not created:
                        if commission.user == request.user:
                            # User owns this commission, redirect to dashboard
                            return redirect(
                                "commorganizer-artist-dashboard",
                                commission_name=commission.name,
                            )
                        else:
                            create_form.add_error(
                                "name",
                                "A commission with this name already exists.",
                            )
                    else:
                        return redirect(
                            "commorganizer-artist-dashboard",
                            commission_name=commission.name,
                        )
                else:
                    # Anonymous user, require password
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


@login_required
def user_commission_select(request):
    """View for logged-in users to select from their commissions"""

    if request.method == "POST" and "delete_commission" in request.POST:
        commission_id = request.POST.get("delete_commission")
        try:
            commission = Commission.objects.get(id=commission_id)

            # Security check: user must own the commission or be staff/moderator
            if (
                commission.user == request.user
                or request.user.is_staff
                or getattr(request.user, "is_moderator", False)
            ):

                commission_name = commission.name
                commission.delete()
                messages.success(
                    request, f"Commission '{commission_name}' has been deleted."
                )
                return redirect("commorganizer-user-select")
            else:
                messages.error(
                    request, "You don't have permission to delete this commission."
                )
        except Commission.DoesNotExist:
            messages.error(request, "Commission not found.")
        except Exception as e:
            messages.error(request, f"Error deleting commission: {str(e)}")

    user_commissions = Commission.objects.filter(user=request.user).order_by(
        "-created_at"
    )

    # Add comment counts to user commissions
    for commission in user_commissions:
        commission.total_comments_count = Comment.objects.filter(
            draft__commission=commission
        ).count()
        commission.resolved_comments_count = Comment.objects.filter(
            draft__commission=commission, resolved=True
        ).count()

    # For moderators/admins, show all commissions
    all_commissions = None
    if request.user.is_staff or getattr(request.user, "is_moderator", False):
        all_commissions = Commission.objects.all().order_by("-created_at")

        # Add comment counts to all commissions
        for commission in all_commissions:
            commission.total_comments_count = Comment.objects.filter(
                draft__commission=commission
            ).count()
            commission.resolved_comments_count = Comment.objects.filter(
                draft__commission=commission, resolved=True
            ).count()

    return render(
        request,
        "commorganizer_user_select.html",
        {
            "user_commissions": user_commissions,
            "all_commissions": all_commissions,
        },
    )


class DraftUploadForm(forms.Form):
    image = forms.ImageField()


class WebhookForm(forms.ModelForm):
    class Meta:
        model = Commission
        fields = ["webhook_url"]
        widgets = {
            "webhook_url": forms.URLInput(
                attrs={
                    "placeholder": "https://discord.com/api/webhooks/...",
                    "size": 60,
                }
            ),
        }


def artist_dashboard(request, commission_name):
    try:
        commission = Commission.objects.get(name=commission_name)
    except Commission.DoesNotExist:
        raise Http404("Commission not found")

    # Security check: user must own the commission, have the password, or be staff/moderator
    if not (
        (request.user.is_authenticated and commission.user == request.user)
        or (
            commission.artist_password
            and request.POST.get("password") == commission.artist_password
        )
        or request.user.is_staff
        or getattr(request.user, "is_moderator", False)
    ):
        # If user is logged in but doesn't own this commission, redirect to selection
        if request.user.is_authenticated:
            messages.error(request, "You don't have access to this commission.")
            return redirect("commorganizer-user-select")
        else:
            # Anonymous user needs password, but only if commission has password protection
            if commission.artist_password:
                return render(
                    request,
                    "commorganizer_password_check.html",
                    {
                        "commission_name": commission_name,
                        "commission": commission,
                    },
                )
            else:
                # Commission is user-owned but user is not logged in
                messages.error(
                    request, "This commission requires a logged-in account to access."
                )
                return redirect("commorganizer")

    # Comments: unresolved first, then resolved, both sorted by age
    unresolved_comments = Comment.objects.filter(
        draft__commission=commission, resolved=False
    ).order_by("created_at")
    resolved_comments = Comment.objects.filter(
        draft__commission=commission, resolved=True
    ).order_by("created_at")
    all_comments = list(unresolved_comments) + list(resolved_comments)

    # Group comments by commenter_name
    comments_by_user = defaultdict(list)
    for c in all_comments:
        comments_by_user[c.commenter_name].append(c)
    comments_by_user = dict(comments_by_user)  # for template

    # Drafts, newest first
    drafts = (
        Draft.objects.filter(commission=commission)
        .order_by("-created_at")
        .annotate(
            unresolved_count=Count("comments", filter=Q(comments__resolved=False))
        )
    )

    # For each draft, calculate satisfied_viewers_count
    for draft in drafts:
        # Use a local variable to avoid overwriting the global comments_by_user
        draft_comments_by_user = defaultdict(list)
        for c in draft.comments.all():
            draft_comments_by_user[c.commenter_name].append(c)
        # Count users where all their comments on this draft are resolved
        draft.satisfied_viewers_count = sum(
            1
            for comments in draft_comments_by_user.values()
            if comments and all(c.resolved for c in comments)
        )

    # Share link
    share_link = request.build_absolute_uri(
        reverse("commorganizer-public-view", args=[commission.name])
    )

    # Webhook form
    webhook_form = WebhookForm(instance=commission)
    if request.method == "POST" and "set_webhook" in request.POST:
        webhook_form = WebhookForm(request.POST, instance=commission)
        if webhook_form.is_valid():
            webhook_form.save()
            return HttpResponseRedirect(request.path)

    # Handle draft upload (stub)
    upload_form = DraftUploadForm()
    if request.method == "POST":
        if "upload_draft" in request.POST:
            upload_form = DraftUploadForm(request.POST, request.FILES)
            if upload_form.is_valid():
                draft = Draft.objects.create(
                    commission=commission, image=upload_form.cleaned_data["image"]
                )
                # Send webhook if set
                if commission.webhook_url:
                    draft_url = (
                        request.build_absolute_uri(
                            reverse("commorganizer-public-view", args=[commission.name])
                        )
                        + f"?draft={draft.pk}"
                    )
                    send_discord_webhook(
                        commission.webhook_url,
                        f"New draft #{draft.number} uploaded for commission '{commission.name}'.\n [Link]({draft_url})",
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

        # Delete comment
        elif "delete_comment" in request.POST:
            comment_id = request.POST.get("delete_comment")
            try:
                comment = Comment.objects.get(
                    pk=comment_id, draft__commission=commission
                )
                comment.delete()
                return HttpResponseRedirect(request.path)
            except Comment.DoesNotExist:
                pass

    return render(
        request,
        "commorganizer_artist_dashboard.html",
        {
            "commission_name": commission_name,
            "comments": all_comments,
            "comments_by_user": comments_by_user,
            "drafts": drafts,
            "share_link": share_link,
            "upload_form": upload_form,
            "webhook_form": webhook_form,
            "commission": commission,
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
    if request.method == "POST" and current_draft:
        if "add_comment" in request.POST:
            x = int(request.POST.get("x", 0))
            y = int(request.POST.get("y", 0))
            commenter_name = request.POST.get("commenter_name", "").strip()[:32]
            content = request.POST.get("content", "").strip()
            if commenter_name and content:
                comment = Comment.objects.create(
                    draft=current_draft,
                    x=x,
                    y=y,
                    commenter_name=commenter_name,
                    content=content,
                )

                # Send webhook if set
                if current_draft.commission.webhook_url:
                    send_discord_webhook(
                        current_draft.commission.webhook_url,
                        f"New comment by {commenter_name} on draft #{current_draft.number} for commission '{commission_name}':\n>>> {content}",
                    )

                # Redirect to same draft after comment
                return redirect(f"{request.path}?draft={current_draft.pk}")

        elif "acknowledge_draft" in request.POST:
            commenter_name = request.POST.get("commenter_name", "").strip()[:32]
            if commenter_name:
                content = f"{commenter_name} acknowledged draft {current_draft.number}"
                comment = Comment.objects.create(
                    draft=current_draft,
                    x=0,
                    y=0,
                    commenter_name=commenter_name,
                    content=content,
                    resolved=True,
                )

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


def api_new_comments(request):
    commission_name = request.GET.get("commission_name")
    since_id = request.GET.get("since_id")
    if not commission_name:
        return JsonResponse({"error": "Missing commission_name"}, status=400)
    try:
        commission = Commission.objects.get(name=commission_name)
    except Commission.DoesNotExist:
        return JsonResponse({"error": "Commission not found"}, status=404)
    comments_qs = Comment.objects.filter(draft__commission=commission)
    if since_id:
        try:
            since_id = int(since_id)
            comments_qs = comments_qs.filter(id__gt=since_id)
        except ValueError:
            pass  # Ignore invalid since_id
    comments_qs = comments_qs.order_by("id")
    data = [
        {
            "id": c.id,
            "draft_number": c.draft.number,
            "x": c.x,
            "y": c.y,
            "commenter_name": c.commenter_name,
            "resolved": c.resolved,
            "content": c.content,
            "created_at": c.created_at.isoformat(),
        }
        for c in comments_qs
    ]
    return JsonResponse({"comments": data})
