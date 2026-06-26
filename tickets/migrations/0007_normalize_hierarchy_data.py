from django.db import migrations


OLD_TO_NEW_DEPARTMENT = {
    "DIRECAO": "DIRETORIA",
    "VICE_DIRECAO": "VICE_DIRETORIA",
    "COORDENACAO_TECNICA": "COORDENACAO_TECNICA",
    "LABORATORIO_ENSINO": "LABORATORIOS",
    "SECRETARIA_ESCOLAR": "SECRETARIA",
    "PSICOLOGIA_ESCOLAR": "PSICOLOGIA",
    "TI": "TI",
}


DEPARTMENT_TO_AREA = {
    "DIRETORIA": "DIRETORIA",
    "VICE_DIRETORIA": "VICE_DIRETORIA",
    "TI": "VICE_DIRETORIA",
    "PSICOLOGIA": "VICE_DIRETORIA",
    "SEGURANCA": "VICE_DIRETORIA",
    "ZELADORIA": "VICE_DIRETORIA",
    "COZINHA": "VICE_DIRETORIA",
    "MANUTENCAO": "VICE_DIRETORIA",
    "ESTAGIO": "VICE_DIRETORIA",
    "MONITORIA": "VICE_DIRETORIA",
    "SECRETARIA": "SECRETARIA",
    "STAI": "STAI",
    "COORDENACAO_PEDAGOGICA": "COORDENACAO_PEDAGOGICA",
    "COORDENACAO_TECNICA": "COORDENACAO_PEDAGOGICA",
    "BIBLIOTECA": "COORDENACAO_PEDAGOGICA",
    "LABORATORIOS": "COORDENACAO_PEDAGOGICA",
    "DOCENCIA": "COORDENACAO_PEDAGOGICA",
}


OLD_USER_AREA_TO_TARGET = {
    "DIRECAO": ("DIRETORIA", "DIRETORIA", "DIRETOR"),
    "VICE_DIRECAO": ("VICE_DIRETORIA", "VICE_DIRETORIA", "VICE_DIRETOR"),
    "TI": ("VICE_DIRETORIA", "TI", "TEC_INFORMATICA"),
    "COORDENACAO_PEDAGOGICA": ("COORDENACAO_PEDAGOGICA", "COORDENACAO_PEDAGOGICA", "COORD_PEDAGOGICO"),
    "COORDENACAO_TECNICA": ("COORDENACAO_PEDAGOGICA", "COORDENACAO_TECNICA", "COORD_TECNICO"),
    "BIBLIOTECA": ("COORDENACAO_PEDAGOGICA", "BIBLIOTECA", "BIBLIOTECARIO"),
    "LABORATORIO_ENSINO": ("COORDENACAO_PEDAGOGICA", "LABORATORIOS", "TEC_LABORATORIO"),
    "STAI": ("STAI", "STAI", "COORDENADOR_STAI"),
    "SECRETARIA_ESCOLAR": ("SECRETARIA", "SECRETARIA", "SECRETARIO"),
    "PSICOLOGIA_ESCOLAR": ("VICE_DIRETORIA", "PSICOLOGIA", "PSICOLOGO"),
}


def normalize_users(apps, schema_editor):
    User = apps.get_model("tickets", "User")
    for user in User.objects.all():
        original_vinculo = user.vinculo
        if original_vinculo in {"HORISTA", "MENSALISTA"}:
            user.vinculo = "PROFESSOR"
            user.area = "COORDENACAO_PEDAGOGICA"
            user.department = "DOCENCIA"
            user.cargo = "PROF_HORISTA" if original_vinculo == "HORISTA" else "PROF_MENSALISTA"
        elif user.area in OLD_USER_AREA_TO_TARGET:
            new_area, new_department, new_cargo = OLD_USER_AREA_TO_TARGET[user.area]
            user.area = new_area
            user.department = new_department
            if user.cargo in {"TI", "DIRECAO", "VICE_DIRECAO", "COORDENACAO_PEDAGOGICA", "COORDENACAO_TECNICA", "BIBLIOTECA", "LABORATORIO_ENSINO", "STAI", "SECRETARIA_ESCOLAR", "PSICOLOGIA_ESCOLAR", "PROFESSOR", "OUTRO"}:
                user.cargo = new_cargo

        if user.department in OLD_TO_NEW_DEPARTMENT:
            user.department = OLD_TO_NEW_DEPARTMENT[user.department]
        if not user.area and user.department in DEPARTMENT_TO_AREA:
            user.area = DEPARTMENT_TO_AREA[user.department]
        user.save(update_fields=["vinculo", "area", "department", "cargo", "is_staff"])


def normalize_tickets(apps, schema_editor):
    Ticket = apps.get_model("tickets", "Ticket")
    TicketCategory = apps.get_model("tickets", "TicketCategory")
    for category in TicketCategory.objects.all():
        if category.department in OLD_TO_NEW_DEPARTMENT:
            category.department = OLD_TO_NEW_DEPARTMENT[category.department]
            category.save(update_fields=["department"])

    for ticket in Ticket.objects.all():
        if ticket.department in OLD_TO_NEW_DEPARTMENT:
            ticket.department = OLD_TO_NEW_DEPARTMENT[ticket.department]
        if not ticket.area and ticket.department in DEPARTMENT_TO_AREA:
            ticket.area = DEPARTMENT_TO_AREA[ticket.department]
        elif ticket.area in OLD_USER_AREA_TO_TARGET:
            ticket.area = OLD_USER_AREA_TO_TARGET[ticket.area][0]
        ticket.save(update_fields=["area", "department"])


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0006_user_department_ticket_area"),
    ]

    operations = [
        migrations.RunPython(normalize_users, migrations.RunPython.noop),
        migrations.RunPython(normalize_tickets, migrations.RunPython.noop),
    ]
