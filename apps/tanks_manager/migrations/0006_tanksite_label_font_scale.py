from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tanks_manager", "0005_alter_tanksite_stage_fg_label_profile"),
    ]

    operations = [
        migrations.AddField(
            model_name="tanksite",
            name="label_font_scale",
            field=models.PositiveSmallIntegerField(
                default=100,
                help_text="Liquid label size as % of default (i might remove this!)",
            ),
        ),
    ]
