from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TankSettings",
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
                ("tank_top_offset", models.PositiveIntegerField(default=360)),
                ("tank_bottom_offset", models.PositiveIntegerField(default=101)),
            ],
            options={
                "verbose_name_plural": "Tank settings",
            },
        ),
        migrations.CreateModel(
            name="TankClone",
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
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("name", models.CharField(max_length=200)),
                ("banner", models.CharField(blank=True, max_length=200)),
                (
                    "image",
                    models.CharField(
                        blank=True,
                        help_text="Relative path or URL if not using upload",
                        max_length=500,
                    ),
                ),
                (
                    "image_file",
                    models.ImageField(
                        blank=True,
                        max_length=500,
                        null=True,
                        upload_to="tanks/clones/",
                    ),
                ),
                ("url", models.CharField(blank=True, max_length=500)),
            ],
            options={
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.CreateModel(
            name="TankLiquid",
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
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("name", models.CharField(max_length=200)),
                ("volume", models.PositiveSmallIntegerField(default=0)),
                ("color", models.CharField(default="#ffffff", max_length=32)),
                ("url", models.CharField(blank=True, max_length=500)),
                ("image", models.CharField(blank=True, max_length=500)),
                (
                    "image_file",
                    models.ImageField(
                        blank=True,
                        max_length=500,
                        null=True,
                        upload_to="tanks/liquids/",
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.CreateModel(
            name="TankLog",
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
                ("date", models.PositiveIntegerField(help_text="Unix timestamp")),
                ("text", models.TextField()),
            ],
            options={
                "ordering": ["date", "id"],
            },
        ),
    ]
