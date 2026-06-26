from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0005_changelog"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="department",
            field=models.CharField(default="", max_length=40),
        ),
        migrations.AddField(
            model_name="ticket",
            name="area",
            field=models.CharField(default="", max_length=40),
        ),
    ]
