from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from datetime import timedelta


ADMIN_CARGOS = {
    "TEC_INFORMATICA",
    "DIRETOR",
    "VICE_DIRETOR",
    "TI",
    "DIRECAO",
    "VICE_DIRECAO",
}


VINCULO_CHOICES = [
    ("ADMINISTRATIVO", "Funcionario administrativo"),
    ("PROFESSOR", "Professor"),
]

AREA_CHOICES = [
    ("TI", "Tecnologia da Informacao"),
    ("DIRECAO", "Direcao"),
    ("VICE_DIRECAO", "Vice-Direcao"),
    ("COORDENACAO_PEDAGOGICA", "Coordenacao Pedagogica"),
    ("COORDENACAO_TECNICA", "Coordenacao Tecnica"),
    ("BIBLIOTECA", "Biblioteca"),
    ("LABORATORIO_ENSINO", "Tecnico de Laboratorio de Ensino"),
    ("STAI", "Coordenacao de STAI"),
    ("SECRETARIA_ESCOLAR", "Secretaria Escolar"),
    ("PSICOLOGIA_ESCOLAR", "Psicologia Escolar"),
    ("DOCENCIA", "Docencia"),
]


CARGO_CHOICES_BY_AREA = {
    "TI": [
        ("TEC_INFORMATICA", "Tecnico de Informatica"),
    ],
    "DIRECAO": [
        ("DIRETOR", "Diretor(a)"),
        ("VICE_DIRETOR", "Vice-diretor(a)"),
    ],
    "VICE_DIRECAO": [
        ("VICE_DIRETOR", "Vice-diretor(a)"),
        ("ASSISTENTE_VICE_DIRECAO", "Assistente da Vice-direcao"),
    ],
    "COORDENACAO_PEDAGOGICA": [
        ("COORD_PEDAGOGICO", "Coordenador(a) Pedagogico(a)"),
        ("COORD_TECNICO", "Coordenador(a) Tecnico(a)"),
        ("ASSISTENTE_COORDENACAO", "Assistente de coordenacao"),
        ("TECNICO_EDUCACIONAL", "Tecnico educacional"),
        ("ASSISTENTE_EDUCACIONAL", "Assistente educacional"),
    ],
    "COORDENACAO_TECNICA": [
        ("COORD_TECNICO", "Coordenador(a) Tecnico(a)"),
        ("ASSISTENTE_COORD_TECNICA", "Assistente de coordenacao tecnica"),
        ("TECNICO_EDUCACIONAL", "Tecnico educacional"),
        ("ASSISTENTE_EDUCACIONAL", "Assistente educacional"),
    ],
    "BIBLIOTECA": [
        ("BIBLIOTECARIO", "Bibliotecario(a)"),
        ("AUXILIAR_BIBLIOTECA", "Auxiliar de biblioteca"),
    ],
    "LABORATORIO_ENSINO": [
        ("TECNICO_LABORATORIO", "Tecnico de laboratorio de ensino"),
    ],
    "STAI": [
        ("COORD_STAI", "Coordenador(a) de STAI"),
        ("ASSISTENTE_STAI", "Assistente de STAI"),
    ],
    "SECRETARIA_ESCOLAR": [
        ("SECRETARIO_ESCOLAR", "Secretario(a) escolar"),
        ("ASSISTENTE_SECRETARIA", "Assistente de secretaria"),
        ("AUXILIAR_SECRETARIA", "Auxiliar de secretaria"),
    ],
    "PSICOLOGIA_ESCOLAR": [
        ("PSICOLOGO_ESCOLAR", "Psicologo(a) escolar"),
        ("ASSISTENTE_PSICOLOGIA", "Assistente de psicologia"),
    ],
    "DOCENCIA": [
        ("HORISTA", "Horista"),
        ("MENSALISTA", "Mensalista"),
    ],
}

CARGO_CHOICES = []
for cargo_group in CARGO_CHOICES_BY_AREA.values():
    for choice in cargo_group:
        if choice not in CARGO_CHOICES:
            CARGO_CHOICES.append(choice)


DEPARTMENT_CHOICES = [
    ("DIRECAO", "Direcao"),
    ("VICE_DIRECAO", "Vice-Direcao"),
    ("COORDENACAO_PEDAGOGICA", "Coordenacao Pedagogica"),
    ("COORDENACAO_TECNICA", "Coordenacao Tecnica"),
    ("BIBLIOTECA", "Biblioteca"),
    ("LABORATORIO_ENSINO", "Tecnico de Laboratorio de Ensino"),
    ("STAI", "Coordenacao de STAI"),
    ("SECRETARIA_ESCOLAR", "Secretaria Escolar"),
    ("TI", "Tecnico de Informatica (TI)"),
    ("PSICOLOGIA_ESCOLAR", "Psicologia Escolar"),
]


TICKET_STATUS = [
    ("OPEN", "Aberto"),
    ("IN_PROGRESS", "Em tratativa"),
    ("FORWARDED", "Encaminhado"),
    ("CLOSED", "Encerrado"),
    ("DONE", "Concluido"),
]


TICKET_URGENCY = [
    ("LOW", "Baixa"),
    ("MEDIUM", "Media"),
    ("HIGH", "Alta"),
]


COMMENT_KIND = [
    ("COMMENT", "Comentario"),
    ("STATUS", "Mudanca de status"),
    ("TRANSFER", "Transferencia"),
    ("REOPEN", "Reabertura"),
]


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, matricula, email, password, **extra_fields):
        if not matricula:
            raise ValueError("A matricula e obrigatoria.")
        if not email:
            raise ValueError("O e-mail e obrigatorio.")
        email = self.normalize_email(email)
        user = self.model(matricula=matricula, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, matricula, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(matricula, email, password, **extra_fields)

    def create_superuser(self, matricula, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("full_name", "Administrador")
        extra_fields.setdefault("area", "TI")
        extra_fields.setdefault("cargo", "TEC_INFORMATICA")
        extra_fields.setdefault("vinculo", "ADMINISTRATIVO")
        return self._create_user(matricula, email, password, **extra_fields)


class User(AbstractUser):
    username = None
    objects = UserManager()

    matricula = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    vinculo = models.CharField(max_length=40, choices=VINCULO_CHOICES, default="ADMINISTRATIVO")
    area = models.CharField(max_length=40, choices=AREA_CHOICES, blank=True, default="")
    cargo = models.CharField(max_length=40, choices=CARGO_CHOICES, default="TEC_INFORMATICA")
    phone = models.CharField(max_length=30, blank=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "matricula"
    REQUIRED_FIELDS = ["email", "full_name"]

    def save(self, *args, **kwargs):
        self.is_staff = self.cargo in ADMIN_CARGOS or self.is_superuser
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.vinculo == "PROFESSOR":
            if self.area and self.area != "DOCENCIA":
                raise ValidationError({"area": "Professor deve ficar na area Docencia."})
            if self.cargo not in {"HORISTA", "MENSALISTA"}:
                raise ValidationError({"cargo": "Professor deve ser Horista ou Mensalista."})
            self.area = "DOCENCIA"
            return

        if self.vinculo == "ADMINISTRATIVO":
            if not self.area:
                raise ValidationError({"area": "Informe a area do funcionario administrativo."})
            allowed_cargos = {code for code, _label in CARGO_CHOICES_BY_AREA.get(self.area, [])}
            if self.cargo not in allowed_cargos:
                raise ValidationError({"cargo": "Cargo invalido para a area selecionada."})
            return

        raise ValidationError({"vinculo": "Vinculo invalido."})

    @property
    def is_admin_role(self):
        return self.cargo in ADMIN_CARGOS

    def __str__(self):
        area = self.get_area_display() if self.area else "Sem area"
        return f"{self.full_name} ({self.matricula}) - {area} / {self.get_cargo_display()}"


class Announcement(models.Model):
    title = models.CharField(max_length=120)
    body = models.TextField()
    image = models.ImageField(upload_to="announcements/", blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="announcements")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def gallery_items(self):
        items = []
        if self.image:
            items.append(
                {
                    "url": self.image.url,
                    "alt": self.title,
                    "source": "legacy",
                }
            )
        for media in self.announcement_images.all():
            items.append(
                {
                    "url": media.image.url,
                    "alt": self.title,
                    "source": "gallery",
                }
            )
        return items

    def __str__(self):
        return self.title


class AnnouncementImage(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name="announcement_images")
    image = models.ImageField(upload_to="announcements/")
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "created_at", "pk"]

    def __str__(self):
        return f"{self.announcement_id} - {self.pk}"


class TicketCategory(models.Model):
    department = models.CharField(max_length=40, choices=DEPARTMENT_CHOICES)
    name = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["department", "name"]
        unique_together = [("department", "name")]

    def __str__(self):
        return f"{self.get_department_display()} - {self.name}"


class Ticket(models.Model):
    DEADLINE_BY_URGENCY_HOURS = {
        "HIGH": 24,
        "MEDIUM": 72,
        "LOW": 168,
    }

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="opened_tickets")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="assigned_tickets")
    department = models.CharField(max_length=40, choices=DEPARTMENT_CHOICES)
    category = models.ForeignKey(TicketCategory, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=180)
    description = models.TextField()
    urgency = models.CharField(max_length=10, choices=TICKET_URGENCY, default="LOW")
    status = models.CharField(max_length=20, choices=TICKET_STATUS, default="OPEN")
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    concluded_at = models.DateTimeField(null=True, blank=True)
    reopened_at = models.DateTimeField(null=True, blank=True)
    last_status_change_at = models.DateTimeField(auto_now=True)
    solution_summary = models.TextField(blank=True)
    reopened_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-opened_at"]

    def __str__(self):
        return f"#{self.pk} - {self.title}"

    @property
    def number(self):
        return f"CHM-{self.pk:06d}" if self.pk else "CHM-NEW"

    @property
    def is_closed(self):
        return self.status == "CLOSED"

    @property
    def is_done(self):
        return self.status == "DONE"

    @property
    def deadline_at(self):
        if not self.opened_at:
            return None
        hours = self.DEADLINE_BY_URGENCY_HOURS.get(self.urgency, 168)
        return self.opened_at + timedelta(hours=hours)

    @property
    def is_overdue(self):
        if self.status in {"CLOSED", "DONE"}:
            return False
        deadline_at = self.deadline_at
        return bool(deadline_at and timezone.now() > deadline_at)

    @property
    def deadline_label(self):
        return {
            "HIGH": "24h",
            "MEDIUM": "72h",
            "LOW": "7 dias",
        }.get(self.urgency, "7 dias")


class TicketEvent(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    kind = models.CharField(max_length=20, choices=COMMENT_KIND)
    message = models.TextField()
    from_status = models.CharField(max_length=20, choices=TICKET_STATUS, blank=True)
    to_status = models.CharField(max_length=20, choices=TICKET_STATUS, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.ticket_id} - {self.get_kind_display()}"


def attachment_upload_to(instance, filename):
    ticket_id = instance.ticket_id or "new"
    return f"tickets/{ticket_id}/{filename}"


class TicketAttachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    file = models.FileField(upload_to=attachment_upload_to)
    original_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.original_name and self.file:
            self.original_name = self.file.name.rsplit("/", 1)[-1]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.original_name


def user_can_admin(user):
    return bool(user and user.is_authenticated and (user.is_superuser or getattr(user, "cargo", None) in ADMIN_CARGOS))


def user_can_view_ticket(user, ticket):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user_can_admin(user):
        return True
    return ticket.requester_id == user.id or ticket.assigned_to_id == user.id or ticket.department == user.area


def user_can_edit_ticket(user, ticket):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user_can_admin(user):
        return True
    return ticket.requester_id == user.id or ticket.assigned_to_id == user.id


def user_can_reopen_ticket(user, ticket):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user_can_admin(user):
        return True
    return ticket.requester_id == user.id or ticket.department == user.area
