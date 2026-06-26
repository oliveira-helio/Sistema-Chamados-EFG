from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0004_announcementimage"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChangeLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("entity_type", models.CharField(choices=[("USER", "Usuario"), ("ANNOUNCEMENT", "Comunicado")], max_length=20)),
                ("entity_id", models.PositiveIntegerField()),
                ("action", models.CharField(choices=[("CREATE", "Criacao"), ("UPDATE", "Edicao"), ("PASSWORD", "Troca de senha"), ("ACTIVATE", "Ativacao"), ("DEACTIVATE", "Inativacao"), ("PUBLISH", "Publicacao"), ("UNPUBLISH", "Despublicacao")], max_length=20)),
                ("before_data", models.JSONField(blank=True, default=dict)),
                ("after_data", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="change_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
