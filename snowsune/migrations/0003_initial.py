# Generated by Django 5.1.6 on 2025-06-19 18:15

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("snowsune", "0002_delete_customuser"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteSetting",
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
                ("key", models.CharField(max_length=100, unique=True)),
                ("value", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "Site Setting",
                "verbose_name_plural": "Site Settings",
            },
        ),
    ]
