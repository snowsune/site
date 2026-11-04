from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tanks_manager", "0003_alter_tanksite_owner_fk"),
    ]

    operations = [
        migrations.AddField(
            model_name="tanksite",
            name="stage_fg_label_profile",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Cached [[y_pct_from_top, x_pct], ...] from transparent scanlines; rebuilt on FG upload.",
            ),
        ),
    ]
