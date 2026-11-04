from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vore_day_rumble", "0006_site_voting"),
    ]

    operations = [
        migrations.AddField(
            model_name="contestant",
            name="withdrawn",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Dropped out. But, filsl the space on the bracket"
                    "auto-forfeit to the opponent for upcoming."
                ),
            ),
        ),
    ]
