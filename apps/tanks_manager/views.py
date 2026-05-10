import os
import re
import time
from datetime import datetime, timedelta, timezone as dt_timezone

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.utils.text import slugify
from django.views.decorators.http import require_GET, require_POST

from .models import TankLiquid, TankLog, TankSite, tanks_for_user

# Stage layout: offsets are for an 850px-tall design box (see tank_page.css aspect-ratio).
_DESIGN_STAGE_HEIGHT = 850


def _stage_art_urls(site, request):
    """Absolute URLs for stage layers: uploads, else bundled static defaults."""
    if site.stage_background:
        bg = request.build_absolute_uri(site.stage_background.url)
    else:
        bg = request.build_absolute_uri(
            static("tanks_manager/Alice_close_up_sheath_background.png")
        )
    if site.stage_foreground:
        fg = request.build_absolute_uri(site.stage_foreground.url)
    else:
        fg = request.build_absolute_uri(
            static("tanks_manager/Alice_close_up_sheath_shot.png")
        )
    return bg, fg


def _liquid_layer_rows(liquids, tank_top, tank_bottom, request):
    """Bottom + height as % of design stage height."""
    design = _DESIGN_STAGE_HEIGHT
    tank_h = max(0, design - tank_top - tank_bottom)
    offset_px = 0.0
    cumulative_vol = 0
    rows = []
    for li in liquids:
        vol = int(li.volume)
        h_px = (vol / 100.0) * tank_h
        bottom_px = tank_bottom + offset_px
        cumulative_vol += vol
        if h_px <= 0:
            offset_px += h_px
            continue
        if li.image_file:
            img = request.build_absolute_uri(li.image_file.url)
        elif li.image:
            raw = li.image.strip()
            if raw.startswith(("http://", "https://", "data:")):
                img = raw
            elif raw.startswith("/"):
                img = request.build_absolute_uri(raw)
            else:
                img = request.build_absolute_uri(f"/{raw.lstrip('/')}")
        else:
            img = ""
        rows.append(
            {
                "bottom_pct": (bottom_px / design) * 100,
                "height_pct": (h_px / design) * 100,
                "color": li.color or "#ffffff",
                "image": img,
                "name": li.name,
                "volume": vol,
                "url": li.url.strip(),
                "label_nudge": cumulative_vol < 20,
            }
        )
        offset_px += h_px
    return rows


def _logs_for_show(logs):
    out = []
    now = datetime.now(dt_timezone.utc)
    for g in logs:
        dt = datetime.fromtimestamp(int(g.date), tz=dt_timezone.utc)
        is_new = (now - dt) < timedelta(hours=8)
        out.append({"dt": dt, "text": g.text, "is_new": is_new})
    return out


def _editor_data(site):
    return {
        "liquids": [
            {
                "pk": li.pk,
                "name": li.name,
                "volume": li.volume,
                "color": li.color,
                "url": li.url,
                "image": li.image,
                "upload_preview_url": li.image_file.url if li.image_file else "",
            }
            for li in TankLiquid.objects.filter(tank_site=site)
        ],
        "settings": {
            "tankTopOffset": site.tank_top_offset,
            "tankBottomOffset": site.tank_bottom_offset,
            "character_name": site.character_name,
            "character_url": site.character_url,
            "stage_background_url": site.stage_background.url
            if site.stage_background
            else "",
            "stage_foreground_url": site.stage_foreground.url
            if site.stage_foreground
            else "",
        },
        "logs": [
            {"date": g.date, "text": g.text}
            for g in TankLog.objects.filter(tank_site=site)
        ],
    }


def _idx(post, files, letter):
    rx = re.compile(rf"^{letter}(\d+)_")
    keys = list(post.keys()) + list(files.keys())
    return sorted({int(m.group(1)) for k in keys if (m := rx.match(k))})


def _build(post, files):
    liquids, logs = [], []
    for i in _idx(post, files, "l"):
        raw_pk = post.get(f"l{i}_id", "").strip()
        row = {
            "pk": int(raw_pk) if raw_pk.isdigit() else None,
            "name": post.get(f"l{i}_name", "").strip(),
            "volume": int(post.get(f"l{i}_vol") or 0),
            "color": post.get(f"l{i}_color", "").strip(),
            "url": post.get(f"l{i}_url", "").strip(),
            "image": post.get(f"l{i}_img", "").strip(),
            "_clear_upload": f"l{i}_clearimg" in post,
        }
        k = f"l{i}_imgfile"
        if k in files and getattr(files[k], "name", ""):
            row["_upload"] = files[k]
        liquids.append(row)
    now = int(time.time())
    for i in _idx(post, files, "g"):
        raw = post.get(f"g{i}_date", "").strip()
        try:
            d = int(raw) if raw else now
        except ValueError:
            d = now
        if d == 0:
            d = now
        logs.append({"date": d, "text": post.get(f"g{i}_text", "").strip()})
    return {
        "liquids": liquids,
        "settings": {
            "tankTopOffset": int(post.get("top") or 0),
            "tankBottomOffset": int(post.get("bot") or 0),
            "character_name": post.get("char_name", "").strip()[:200],
            "character_url": post.get("char_url", "").strip()[:500],
        },
        "logs": logs,
    }


def _liquid_change_logs(old_vols, new_liquids):
    new_vols = {row["name"]: row["volume"] for row in new_liquids if row["name"]}
    ts = int(time.time())
    lines = []
    for name, vol in new_vols.items():
        if name not in old_vols:
            lines.append((ts, f"Added {vol}% {name}."))
        elif old_vols[name] != vol:
            lines.append((ts, f"{name}: {old_vols[name]}% → {vol}%."))
    for name in old_vols:
        if name not in new_vols:
            lines.append((ts, f"Removed {name}."))
    return lines


def _snapshot_image_files(model_cls, tank_site):
    by_pk = {}
    for obj in model_cls.objects.filter(tank_site=tank_site):
        if obj.image_file:
            with obj.image_file.open("rb") as fh:
                by_pk[obj.pk] = (obj.image_file.name, fh.read())
    return by_pk


def _save_liquid(row, snap, tank_site):
    pk = row["pk"]
    up = row.get("_upload")
    clear = row.get("_clear_upload")
    obj = TankLiquid.objects.create(
        tank_site=tank_site,
        sort_order=row["_order"],
        name=row["name"],
        volume=row["volume"],
        color=row["color"] or "#ffffff",
        url=row["url"],
        image=row["image"],
    )
    if up:
        obj.image_file.save(up.name, up, save=True)
    elif pk and snap.get(pk) and not clear:
        name, raw = snap[pk]
        obj.image_file.save(os.path.basename(name), ContentFile(raw), save=True)


@require_GET
def tank_show(request, slug):
    site = get_object_or_404(TankSite, slug=slug)
    liquids = TankLiquid.objects.filter(tank_site=site)
    logs = TankLog.objects.filter(tank_site=site)
    bg_url, fg_url = _stage_art_urls(site, request)
    return render(
        request,
        "tanks_manager/tank_show.html",
        {
            "tank_site": site,
            "stage_background_url": bg_url,
            "stage_foreground_url": fg_url,
            "liquid_layers": _liquid_layer_rows(
                liquids, site.tank_top_offset, site.tank_bottom_offset, request
            ),
            "logs": _logs_for_show(logs),
        },
    )


@require_GET
def tanks_hub(request):
    tanks_owned = []
    username_slug_hint = ""
    if request.user.is_authenticated:
        tanks_owned = list(tanks_for_user(request.user))
        username_slug_hint = _tank_slug_from_username(request.user)
    return render(
        request,
        "tanks_manager/hub.html",
        {
            "tanks_owned": tanks_owned,
            "username_slug_hint": username_slug_hint,
        },
    )


def _tank_slug_from_username(user):
    """Preferred slug from login name (slug field rules)."""
    return slugify(user.username) or f"user-{user.pk}"


def _slug_candidates_for_new_tank(user):
    """Yield slug guesses until one is unused (globally unique)."""
    base = _tank_slug_from_username(user)
    yield base
    for n in range(2, 500):
        yield f"{base}-{n}"


@login_required
@require_POST
def create_my_tank(request):
    redirect_to = "tanks_manager:hub"
    requested = slugify((request.POST.get("slug") or "").strip())[:50]

    if requested:
        if TankSite.objects.filter(slug=requested).exists():
            messages.error(
                request,
                "That URL slug is already taken. Pick a different one.",
            )
            return redirect(redirect_to)
        try:
            TankSite.objects.create(owner=request.user, slug=requested)
        except IntegrityError:
            messages.error(
                request,
                "Could not create that slug — try another.",
            )
            return redirect(redirect_to)
        slug = requested
    else:
        slug = None
        for cand in _slug_candidates_for_new_tank(request.user):
            if TankSite.objects.filter(slug=cand).exists():
                continue
            try:
                TankSite.objects.create(owner=request.user, slug=cand)
                slug = cand
                break
            except IntegrityError:
                continue
        if slug is None:
            messages.error(
                request,
                "Could not allocate a URL slug. Try entering one manually.",
            )
            return redirect(redirect_to)

    messages.success(
        request,
        "Tank page created — customize it in the editor.",
    )
    return redirect("tanks_manager:edit", slug=slug)


@transaction.atomic
def _persist(data, tank_site):
    old_vols = {
        li.name: li.volume
        for li in TankLiquid.objects.filter(tank_site=tank_site).order_by("sort_order")
    }
    liquid_snap = _snapshot_image_files(TankLiquid, tank_site)

    tank_site.tank_top_offset = data["settings"]["tankTopOffset"]
    tank_site.tank_bottom_offset = data["settings"]["tankBottomOffset"]
    tank_site.character_name = data["settings"]["character_name"]
    tank_site.character_url = data["settings"]["character_url"]
    tank_site.save(
        update_fields=[
            "tank_top_offset",
            "tank_bottom_offset",
            "character_name",
            "character_url",
        ]
    )

    TankLiquid.objects.filter(tank_site=tank_site).delete()
    for i, row in enumerate(data["liquids"]):
        row["_order"] = i
        _save_liquid(row, liquid_snap, tank_site)

    auto = _liquid_change_logs(old_vols, data["liquids"])
    TankLog.objects.filter(tank_site=tank_site).delete()
    TankLog.objects.bulk_create(
        [
            TankLog(tank_site=tank_site, date=g["date"], text=g["text"])
            for g in data["logs"]
        ]
    )
    if auto:
        TankLog.objects.bulk_create(
            [TankLog(tank_site=tank_site, date=d, text=t) for d, t in auto]
        )


def _can_edit_tank(user, site):
    return user.is_staff or (user.is_authenticated and user.pk == site.owner_id)


@login_required
@require_POST
def delete_my_tank(request, slug):
    site = get_object_or_404(TankSite, slug=slug)
    if not _can_edit_tank(request.user, site):
        raise PermissionDenied
    label = site.character_name or site.slug
    site.delete()
    messages.success(request, f"Deleted “{label}”.")
    return redirect("tanks_manager:hub")


@login_required
def edit(request, slug):
    site = get_object_or_404(TankSite, slug=slug)
    if not _can_edit_tank(request.user, site):
        raise PermissionDenied

    data = _editor_data(site)

    if request.method == "POST" and "save" in request.POST:
        try:
            data = _build(request.POST, request.FILES)
            _persist(data, site)
            site = get_object_or_404(TankSite, slug=slug)
            if request.POST.get("clear_stage_bg"):
                if site.stage_background:
                    site.stage_background.delete(save=False)
                site.stage_background = None
                site.save(update_fields=["stage_background"])
            if request.POST.get("clear_stage_fg"):
                if site.stage_foreground:
                    site.stage_foreground.delete(save=False)
                site.stage_foreground = None
                site.save(update_fields=["stage_foreground"])
            site = get_object_or_404(TankSite, slug=slug)
            if f := request.FILES.get("stage_bg"):
                if getattr(f, "name", ""):
                    site.stage_background.save(f.name, f, save=True)
            if f := request.FILES.get("stage_fg"):
                if getattr(f, "name", ""):
                    site.stage_foreground.save(f.name, f, save=True)
            messages.success(request, "Saved.")
            return redirect("tanks_manager:edit", slug=site.slug)
        except Exception as e:
            messages.error(request, str(e))

    return render(
        request,
        "tanks_manager/edit.html",
        {
            "tank_site": site,
            "data": data,
            "unix_now": int(time.time()),
        },
    )
