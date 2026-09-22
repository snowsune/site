from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0004_blogimage_filefield"),
    ]

    operations = [
        migrations.AddField(
            model_name="blogimage",
            name="checksum",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="blogimage",
            name="size",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
    ]
