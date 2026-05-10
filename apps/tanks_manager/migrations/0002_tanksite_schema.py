import os

from django.conf import settings
from django.core.files import File
from django.db import migrations, models
import django.db.models.deletion


def forwards(apps, schema_editor):
    TankSite = apps.get_model("tanks_manager", "TankSite")
    TankSettings = apps.get_model("tanks_manager", "TankSettings")
    TankLiquid = apps.get_model("tanks_manager", "TankLiquid")
    TankLog = apps.get_model("tanks_manager", "TankLog")
    CustomUser = apps.get_model("users", "CustomUser")

    owner = (
        CustomUser.objects.filter(username="vixi").first()
        or CustomUser.objects.filter(is_superuser=True).first()
        or CustomUser.objects.order_by("pk").first()
    )
    if not owner:
        raise RuntimeError(
            "tanks_manager 0002_tanksite_schema requires at least one users.CustomUser."
        )

    ts = TankSettings.objects.filter(pk=1).first()
    top, bot = 360, 101
    if ts:
        top, bot = ts.tank_top_offset, ts.tank_bottom_offset

    site = TankSite(
        owner_id=owner.pk,
        slug="vixi",
        tank_top_offset=top,
        tank_bottom_offset=bot,
        character_name="",
        character_url="",
    )
    site.save()

    if ts and getattr(ts, "stage_background", None):
        try:
            with ts.stage_background.open("rb") as fh:
                site.stage_background.save(
                    os.path.basename(ts.stage_background.name), File(fh), save=True
                )
        except OSError:
            pass
    if ts and getattr(ts, "stage_foreground", None):
        try:
            with ts.stage_foreground.open("rb") as fh:
                site.stage_foreground.save(
                    os.path.basename(ts.stage_foreground.name), File(fh), save=True
                )
        except OSError:
            pass

    TankLiquid.objects.all().update(tank_site_id=site.pk)
    TankLog.objects.all().update(tank_site_id=site.pk)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("tanks_manager", "0001_initial"),
        ("users", "0004_customuser_email_verification_sent_at_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="TankSite",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        db_index=True,
                        help_text="URL segment, e.g. vixi → /tanks/vixi/",
                        max_length=50,
                        unique=True,
                    ),
                ),
                ("tank_top_offset", models.PositiveIntegerField(default=360)),
                ("tank_bottom_offset", models.PositiveIntegerField(default=101)),
                (
                    "character_name",
                    models.CharField(
                        blank=True,
                        help_text="Shown as the main title on the public tank page when set.",
                        max_length=200,
                    ),
                ),
                (
                    "character_url",
                    models.CharField(
                        blank=True,
                        help_text="Optional; makes the title a link (e.g. profile or ref sheet).",
                        max_length=500,
                    ),
                ),
                (
                    "stage_background",
                    models.ImageField(
                        blank=True,
                        help_text="Optional; sample Alice tank art is used when empty.",
                        max_length=500,
                        null=True,
                        upload_to="tanks/stage/",
                    ),
                ),
                (
                    "stage_foreground",
                    models.ImageField(
                        blank=True,
                        help_text="Optional; sample overlay is used when empty.",
                        max_length=500,
                        null=True,
                        upload_to="tanks/stage/",
                    ),
                ),
                (
                    "owner",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tank_site",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["slug"],
            },
        ),
        migrations.AddField(
            model_name="tankliquid",
            name="tank_site",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="liquids",
                to="tanks_manager.tanksite",
            ),
        ),
        migrations.AddField(
            model_name="tanklog",
            name="tank_site",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="logs",
                to="tanks_manager.tanksite",
            ),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.AlterField(
            model_name="tankliquid",
            name="tank_site",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="liquids",
                to="tanks_manager.tanksite",
            ),
        ),
        migrations.AlterField(
            model_name="tanklog",
            name="tank_site",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="logs",
                to="tanks_manager.tanksite",
            ),
        ),
        migrations.AlterField(
            model_name="tanksite",
            name="owner",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tank_site",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.DeleteModel(
            name="TankClone",
        ),
        migrations.DeleteModel(
            name="TankSettings",
        ),
    ]
