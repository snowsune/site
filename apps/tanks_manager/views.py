import json
import os
import re
import time
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_GET

from .models import TankClone, TankLiquid, TankLog, TankSettings

CLONE_NAME_CHOICES = (
    "Azure",
    "Cyan",
    "Indigo",
    "Lapis",
    "Midnight",
    "Navy",
    "Royal",
    "Sapphire",
    "Sky",
)


def _settings():
    obj, _ = TankSettings.objects.get_or_create(
        pk=1,
        defaults=dict(tank_top_offset=360, tank_bottom_offset=101),
    )
    return obj


def _image_json(obj):
    if obj.image_file:
        base = settings.SITE_URL.rstrip("/")
        return f"{base}{obj.image_file.url}"
    return obj.image or ""


def _liquid_export(li):
    row = {
        "name": li.name,
        "volume": li.volume,
        "color": li.color,
        "url": li.url,
    }
    img = _image_json(li)
    if img:
        row["image"] = img
    return row


def _data_from_db():
    s = _settings()
    return {
        "clones": [
            {
                "name": c.name,
                "banner": c.banner,
                "image": _image_json(c),
                "url": c.url,
            }
            for c in TankClone.objects.all()
        ],
        "liquids": [_liquid_export(li) for li in TankLiquid.objects.all()],
        "settings": {
            "tankTopOffset": s.tank_top_offset,
            "tankBottomOffset": s.tank_bottom_offset,
        },
        "logs": [{"date": g.date, "text": g.text} for g in TankLog.objects.all()],
    }


def _editor_data():
    s = _settings()
    return {
        "clones": [
            {
                "pk": c.pk,
                "name": c.name,
                "banner": c.banner,
                "image": c.image,
                "url": c.url,
                "upload_preview_url": c.image_file.url if c.image_file else "",
            }
            for c in TankClone.objects.all()
        ],
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
            for li in TankLiquid.objects.all()
        ],
        "settings": {
            "tankTopOffset": s.tank_top_offset,
            "tankBottomOffset": s.tank_bottom_offset,
        },
        "logs": [{"date": g.date, "text": g.text} for g in TankLog.objects.all()],
    }


def _idx(post, files, letter):
    rx = re.compile(rf"^{letter}(\d+)_")
    keys = list(post.keys()) + list(files.keys())
    return sorted({int(m.group(1)) for k in keys if (m := rx.match(k))})


def _build(post, files):
    clones, liquids, logs = [], [], []
    for i in _idx(post, files, "c"):
        raw_pk = post.get(f"c{i}_id", "").strip()
        row = {
            "pk": int(raw_pk) if raw_pk.isdigit() else None,
            "name": post.get(f"c{i}_name", "").strip(),
            "banner": post.get(f"c{i}_banner", "").strip(),
            "image": post.get(f"c{i}_image", "").strip(),
            "url": post.get(f"c{i}_url", "").strip(),
            "_clear_upload": f"c{i}_clearimg" in post,
        }
        k = f"c{i}_imgfile"
        if k in files and getattr(files[k], "name", ""):
            row["_upload"] = files[k]
        clones.append(row)
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
        "clones": clones,
        "liquids": liquids,
        "settings": {
            "tankTopOffset": int(post.get("top") or 0),
            "tankBottomOffset": int(post.get("bot") or 0),
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


def _snapshot_image_files(model_cls):
    by_pk = {}
    for obj in model_cls.objects.all():
        if obj.image_file:
            with obj.image_file.open("rb") as fh:
                by_pk[obj.pk] = (obj.image_file.name, fh.read())
    return by_pk


def _save_clone(row, snap):
    pk = row["pk"]
    up = row.get("_upload")
    clear = row.get("_clear_upload")
    obj = TankClone.objects.create(
        sort_order=row["_order"],
        name=row["name"],
        banner=row["banner"],
        image=row["image"],
        url=row["url"],
    )
    if up:
        obj.image_file.save(up.name, up, save=True)
    elif pk and snap.get(pk) and not clear:
        name, raw = snap[pk]
        obj.image_file.save(os.path.basename(name), ContentFile(raw), save=True)


def _save_liquid(row, snap):
    pk = row["pk"]
    up = row.get("_upload")
    clear = row.get("_clear_upload")
    obj = TankLiquid.objects.create(
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


def _dumps(data):
    return json.dumps(data, indent=1, ensure_ascii=False) + "\n"


@require_GET
def data_json(request):
    resp = HttpResponse(_dumps(_data_from_db()), content_type="application/json")
    resp["Access-Control-Allow-Origin"] = "*"
    return resp


@transaction.atomic
def _persist(data):
    old_vols = {li.name: li.volume for li in TankLiquid.objects.order_by("sort_order")}
    clone_snap = _snapshot_image_files(TankClone)
    liquid_snap = _snapshot_image_files(TankLiquid)

    s = _settings()
    s.tank_top_offset = data["settings"]["tankTopOffset"]
    s.tank_bottom_offset = data["settings"]["tankBottomOffset"]
    s.save()

    TankClone.objects.all().delete()
    for i, row in enumerate(data["clones"]):
        row["_order"] = i
        _save_clone(row, clone_snap)

    auto = _liquid_change_logs(old_vols, data["liquids"])
    TankLiquid.objects.all().delete()
    for i, row in enumerate(data["liquids"]):
        row["_order"] = i
        _save_liquid(row, liquid_snap)

    TankLog.objects.all().delete()
    TankLog.objects.bulk_create(
        [TankLog(date=g["date"], text=g["text"]) for g in data["logs"]]
    )
    if auto:
        TankLog.objects.bulk_create([TankLog(date=d, text=t) for d, t in auto])


@staff_member_required
def edit(request):
    err = None
    data = _editor_data()

    if request.method == "POST" and "save" in request.POST:
        try:
            data = _build(request.POST, request.FILES)
            _persist(data)
            messages.success(request, "Saved.")
            return redirect("tanks_manager:edit")
        except Exception as e:
            err = str(e)

    return render(
        request,
        "tanks_manager/edit.html",
        {
            "data": data,
            "err": err,
            "unix_now": int(time.time()),
            "clone_names": CLONE_NAME_CHOICES,
            "clone_names_json": mark_safe(json.dumps(CLONE_NAME_CHOICES)),
        },
    )
