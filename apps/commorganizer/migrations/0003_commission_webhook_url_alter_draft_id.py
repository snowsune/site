# Generated by Django 5.1.6 on 2025-07-17 18:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("commorganizer", "0002_draft_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="commission",
            name="webhook_url",
            field=models.URLField(
                blank=True,
                help_text="Optional: Discord webhook for notifications.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="draft",
            name="id",
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
