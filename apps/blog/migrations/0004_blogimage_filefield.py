from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0003_comment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="blogimage",
            name="image",
            field=models.FileField(max_length=500, upload_to="blog/uploads/"),
        ),
    ]
