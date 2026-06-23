from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import tickets.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now)),
                ("matricula", models.CharField(max_length=30, unique=True)),
                ("full_name", models.CharField(max_length=150)),
                ("vinculo", models.CharField(choices=[("COLABORADOR_ADMINISTRATIVO", "Colaborador administrativo"), ("PROFESSOR", "Professor"), ("HORISTA", "Horista"), ("MENSALISTA", "Mensalista")], default="COLABORADOR_ADMINISTRATIVO", max_length=40)),
                ("cargo", models.CharField(choices=[("TI", "Tecnico de Informatica (TI)"), ("DIRECAO", "Direcao"), ("VICE_DIRECAO", "Vice-Direcao"), ("COORDENACAO_PEDAGOGICA", "Coordenacao Pedagogica"), ("COORDENACAO_TECNICA", "Coordenacao Tecnica"), ("BIBLIOTECA", "Biblioteca"), ("LABORATORIO_ENSINO", "Tecnico de Laboratorio de Ensino"), ("STAI", "Coordenacao de STAI"), ("SECRETARIA_ESCOLAR", "Secretaria Escolar"), ("PSICOLOGIA_ESCOLAR", "Psicologia Escolar"), ("PROFESSOR", "Professor"), ("OUTRO", "Outro")], default="OUTRO", max_length=40)),
                ("phone", models.CharField(blank=True, max_length=30)),
                ("groups", models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={
                "verbose_name": "usuario",
                "verbose_name_plural": "usuarios",
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Announcement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                ("body", models.TextField()),
                ("is_published", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="announcements", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="TicketCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("department", models.CharField(choices=[("DIRECAO", "Direcao"), ("VICE_DIRECAO", "Vice-Direcao"), ("COORDENACAO_PEDAGOGICA", "Coordenacao Pedagogica"), ("COORDENACAO_TECNICA", "Coordenacao Tecnica"), ("BIBLIOTECA", "Biblioteca"), ("LABORATORIO_ENSINO", "Tecnico de Laboratorio de Ensino"), ("STAI", "Coordenacao de STAI"), ("SECRETARIA_ESCOLAR", "Secretaria Escolar"), ("TI", "Tecnico de Informatica (TI)"), ("PSICOLOGIA_ESCOLAR", "Psicologia Escolar")], max_length=40)),
                ("name", models.CharField(max_length=140)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["department", "name"],
                "unique_together": {("department", "name")},
            },
        ),
        migrations.CreateModel(
            name="Ticket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("department", models.CharField(choices=[("DIRECAO", "Direcao"), ("VICE_DIRECAO", "Vice-Direcao"), ("COORDENACAO_PEDAGOGICA", "Coordenacao Pedagogica"), ("COORDENACAO_TECNICA", "Coordenacao Tecnica"), ("BIBLIOTECA", "Biblioteca"), ("LABORATORIO_ENSINO", "Tecnico de Laboratorio de Ensino"), ("STAI", "Coordenacao de STAI"), ("SECRETARIA_ESCOLAR", "Secretaria Escolar"), ("TI", "Tecnico de Informatica (TI)"), ("PSICOLOGIA_ESCOLAR", "Psicologia Escolar")], max_length=40)),
                ("title", models.CharField(max_length=180)),
                ("description", models.TextField()),
                ("urgency", models.CharField(choices=[("LOW", "Baixa"), ("MEDIUM", "Media"), ("HIGH", "Alta")], default="LOW", max_length=10)),
                ("status", models.CharField(choices=[("OPEN", "Aberto"), ("IN_PROGRESS", "Em tratativa"), ("FORWARDED", "Encaminhado"), ("CLOSED", "Encerrado"), ("DONE", "Concluido")], default="OPEN", max_length=20)),
                ("opened_at", models.DateTimeField(auto_now_add=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("concluded_at", models.DateTimeField(blank=True, null=True)),
                ("reopened_at", models.DateTimeField(blank=True, null=True)),
                ("last_status_change_at", models.DateTimeField(auto_now=True)),
                ("solution_summary", models.TextField(blank=True)),
                ("reopened_count", models.PositiveIntegerField(default=0)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="assigned_tickets", to=settings.AUTH_USER_MODEL)),
                ("category", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="tickets.ticketcategory")),
                ("requester", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="opened_tickets", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-opened_at"],
            },
        ),
        migrations.CreateModel(
            name="TicketEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("COMMENT", "Comentario"), ("STATUS", "Mudanca de status"), ("TRANSFER", "Transferencia"), ("REOPEN", "Reabertura")], max_length=20)),
                ("message", models.TextField()),
                ("from_status", models.CharField(blank=True, choices=[("OPEN", "Aberto"), ("IN_PROGRESS", "Em tratativa"), ("FORWARDED", "Encaminhado"), ("CLOSED", "Encerrado"), ("DONE", "Concluido")], max_length=20)),
                ("to_status", models.CharField(blank=True, choices=[("OPEN", "Aberto"), ("IN_PROGRESS", "Em tratativa"), ("FORWARDED", "Encaminhado"), ("CLOSED", "Encerrado"), ("DONE", "Concluido")], max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="tickets.ticket")),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="TicketAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to=tickets.models.attachment_upload_to)),
                ("original_name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="tickets.ticket")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

