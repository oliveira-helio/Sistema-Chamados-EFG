from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0003_announcement_image"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnnouncementImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="announcements/")),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "announcement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="announcement_images",
                        to="tickets.announcement",
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order", "created_at", "pk"],
            },
        ),
    ]
