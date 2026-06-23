from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="area",
            field=models.CharField(blank=True, default="", max_length=40),
        ),
    ]

