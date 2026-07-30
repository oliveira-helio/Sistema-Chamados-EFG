from datetime import timedelta

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db import transaction
from django.utils import timezone

from .models import (
    Ticket,
    TicketEvent,
    managed_departments_for_user,
    user_can_admin,
    user_can_manage_ticket_responsible,
)


SYSTEM_USER_MATRICULA = "SISTEMA"
SYSTEM_USER_EMAIL = "sistema@local.invalid"
SYSTEM_USER_NAME = "Sistema"


def get_system_user():
    User = get_user_model()
    user, created = User.objects.get_or_create(
        matricula=SYSTEM_USER_MATRICULA,
        defaults={
            "email": SYSTEM_USER_EMAIL,
            "full_name": SYSTEM_USER_NAME,
            "vinculo": "ADMINISTRATIVO",
            "area": "VICE_DIRETORIA",
            "department": "TI",
            "cargo": "TEC_INFORMATICA",
            "is_active": False,
        },
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password", "is_staff", "is_active"])
    else:
        changed = False
        for field, value in {
            "email": SYSTEM_USER_EMAIL,
            "full_name": SYSTEM_USER_NAME,
            "vinculo": "ADMINISTRATIVO",
            "area": "VICE_DIRETORIA",
            "department": "TI",
            "cargo": "TEC_INFORMATICA",
            "is_active": False,
        }.items():
            if getattr(user, field) != value:
                setattr(user, field, value)
                changed = True
        if changed:
            user.set_unusable_password()
            user.save()
    return user


def ticket_status_choices_for(user, ticket):
    if not user or not user.is_authenticated or not getattr(user, "is_active", True) or ticket.status == "DONE":
        return []

    can_admin = user.is_superuser or user_can_admin(user)
    can_assigned = ticket.assigned_to_id == user.id
    is_requester = ticket.requester_id == user.id

    if ticket.status == "CLOSED":
        if is_requester or can_admin or can_assigned:
            choices = [
                ("OPEN", "Reabrir chamado"),
                ("DONE", "Concluir chamado"),
            ]
            return [choice for choice in choices if choice[0] != ticket.status]
        return []

    if can_admin or can_assigned:
        choices = [
            ("IN_PROGRESS", "Em tratativa"),
            ("FORWARDED", "Encaminhado"),
            ("CLOSED", "Encerrar"),
        ]
        return [choice for choice in choices if choice[0] != ticket.status]

    return []


def can_change_ticket_status(user, ticket, new_status):
    if new_status == ticket.status:
        return False
    allowed = {value for value, _label in ticket_status_choices_for(user, ticket)}
    return new_status in allowed


def format_ticket_status_message(ticket, old_status, new_status, actor):
    actor_name = actor.full_name if getattr(actor, "full_name", None) else "Sistema"
    actor_role = actor.get_cargo_display() if getattr(actor, "cargo", None) else "Sistema"
    actor_label = f"{actor_name} - {actor_role}"
    status_labels = dict(Ticket._meta.get_field("status").choices)
    old_label = status_labels.get(old_status, old_status)
    new_label = dict(Ticket._meta.get_field("status").choices).get(new_status, new_status)
    if old_status == "CLOSED" and new_status == "OPEN":
        return f"Chamado reaberto de {old_label} para {new_label} por {actor_label}."
    return f"Status alterado de {old_label} para {new_label} por {actor_label}."


@transaction.atomic
def apply_ticket_status_change(ticket, actor, new_status, message=""):
    old_status = ticket.status
    if new_status == old_status:
        raise ValidationError("O chamado já está neste status.")
    ticket.status = new_status
    if new_status == "CLOSED":
        ticket.closed_at = ticket.closed_at or timezone.now()
    elif new_status == "DONE":
        ticket.concluded_at = ticket.concluded_at or timezone.now()
    elif new_status == "OPEN" and old_status == "CLOSED":
        ticket.reopened_at = timezone.now()
        ticket.reopened_count += 1
    ticket.save(update_fields=["status", "closed_at", "concluded_at", "reopened_at", "reopened_count", "last_status_change_at"])

    event_message = message.strip() if message and message.strip() else format_ticket_status_message(ticket, old_status, new_status, actor)
    kind = "REOPEN" if old_status == "CLOSED" and new_status == "OPEN" else "STATUS"
    event = TicketEvent.objects.create(
        ticket=ticket,
        actor=actor,
        kind=kind,
        message=event_message,
        from_status=old_status,
        to_status=new_status,
    )
    return event


def format_responsible_change_message(ticket, old_responsible, new_responsible, actor):
    actor_name = actor.full_name if getattr(actor, "full_name", None) else "Sistema"
    actor_role = actor.get_cargo_display() if getattr(actor, "cargo", None) else "Sistema"
    actor_label = f"{actor_name} - {actor_role}"
    old_label = "Sem responsável"
    if old_responsible:
        old_label = f"{old_responsible.full_name} - {old_responsible.get_cargo_display()}"
    new_label = f"{new_responsible.full_name} - {new_responsible.get_cargo_display()}"
    return f"Responsável alterado de {old_label} para {new_label} por {actor_label}."


def assignable_users_for(user, ticket):
    User = get_user_model()
    if not user_can_manage_ticket_responsible(user, ticket):
        return User.objects.none()

    departments = managed_departments_for_user(user)
    qs = User.objects.filter(is_active=True, department__in=departments).order_by("full_name", "matricula")
    if getattr(user, "cargo", "") == "COORD_TECNICO":
        qs = qs.exclude(cargo="COORD_PEDAGOGICO")
    return qs


def close_overdue_tickets():
    system_user = get_system_user()
    cutoff = timezone.now() - timedelta(days=3)
    tickets = Ticket.objects.filter(status="CLOSED", concluded_at__isnull=True).filter(
        Q(closed_at__lte=cutoff) | Q(closed_at__isnull=True, last_status_change_at__lte=cutoff)
    )
    processed = 0
    for ticket in tickets.select_related("requester", "assigned_to", "category"):
        apply_ticket_status_change(
            ticket,
            system_user,
            "DONE",
            "Chamado concluído automaticamente pelo sistema após 3 dias em encerrado.",
        )
        processed += 1
    return processed
