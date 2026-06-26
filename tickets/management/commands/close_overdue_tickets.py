from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from tickets.models import Ticket, TicketEvent


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
            "area": "TI",
            "cargo": "TEC_INFORMATICA",
            "is_active": False,
        },
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password", "is_staff", "is_active"])
    return user


@transaction.atomic
def close_overdue_tickets():
    system_user = get_system_user()
    cutoff = timezone.now() - timedelta(days=3)
    tickets = Ticket.objects.filter(status="CLOSED", concluded_at__isnull=True).filter(
        Q(closed_at__lte=cutoff) | Q(closed_at__isnull=True, last_status_change_at__lte=cutoff)
    )

    processed = 0
    for ticket in tickets.select_related("requester", "assigned_to", "category"):
        old_status = ticket.status
        ticket.status = "DONE"
        ticket.concluded_at = ticket.concluded_at or timezone.now()
        ticket.save(update_fields=["status", "concluded_at", "last_status_change_at"])
        TicketEvent.objects.create(
            ticket=ticket,
            actor=system_user,
            kind="STATUS",
            message="Chamado concluido automaticamente pelo sistema apos 3 dias em encerrado.",
            from_status=old_status,
            to_status="DONE",
        )
        processed += 1

    return processed


class Command(BaseCommand):
    help = "Conclui automaticamente chamados encerrados ha mais de 3 dias."

    def handle(self, *args, **options):
        processed = close_overdue_tickets()
        self.stdout.write(self.style.SUCCESS(f"Chamados concluidos automaticamente: {processed}"))
