from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0002_user_area"),
    ]

    operations = [
        migrations.AddField(
            model_name="announcement",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="announcements/"),
        ),
    ]

