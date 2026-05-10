from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tanks_manager", "0002_tanksite_schema"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tanksite",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tank_sites",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
