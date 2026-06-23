from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
import json

from .forms import (
    AnnouncementForm,
    LoginForm,
    UserAdminForm,
    UserUpdateForm,
    TicketAttachmentForm,
    TicketCreateForm,
    TicketEventForm,
    TicketStatusForm,
)
from .models import (
    Announcement,
    AnnouncementImage,
    CARGO_CHOICES_BY_AREA,
    Ticket,
    TicketAttachment,
    TicketEvent,
    TicketCategory,
    User,
    user_can_admin,
    user_can_edit_ticket,
    user_can_reopen_ticket,
    user_can_view_ticket,
)


def _announcement_gallery_payload(announcement):
    images = announcement.gallery_items
    return {
        "announcement": announcement,
        "images": images,
        "images_json": json.dumps(images),
        "image_count": len(images),
    }


def home(request):
    announcements = [
        _announcement_gallery_payload(announcement)
        for announcement in Announcement.objects.prefetch_related("announcement_images").filter(is_published=True)[:5]
    ]
    open_tickets_count = 0
    open_tickets_count_display = "00"
    if request.user.is_authenticated:
        open_tickets_count = request.user.opened_tickets.filter(status="OPEN").count()
        open_tickets_count_display = f"{open_tickets_count:02d}"
    return render(
        request,
        "tickets/home.html",
        {
            "announcements": announcements,
            "open_tickets_count": open_tickets_count,
            "open_tickets_count_display": open_tickets_count_display,
        },
    )


@login_required
def ticket_categories_api(request):
    department = request.GET.get("department", "").strip()
    categories = []
    if department:
        categories = list(
            TicketCategory.objects.filter(department=department, is_active=True).values("id", "name")
        )
    return JsonResponse({"categories": categories})


@login_required
def user_roles_api(request):
    vinculo = request.GET.get("vinculo", "").strip()
    area = request.GET.get("area", "").strip()

    if vinculo == "PROFESSOR":
        roles = list(CARGO_CHOICES_BY_AREA["DOCENCIA"])
    elif vinculo == "ADMINISTRATIVO" and area in CARGO_CHOICES_BY_AREA:
        roles = list(CARGO_CHOICES_BY_AREA[area])
    else:
        roles = []
    return JsonResponse({"roles": [{"value": value, "label": label} for value, label in roles]})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "Bem-vindo ao sistema de chamados.")
        return redirect("home")
    return render(request, "registration/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, "Voce saiu do sistema.")
    return redirect("login")


def _visible_tickets_for(user, queryset=None):
    qs = queryset or Ticket.objects.select_related("requester", "assigned_to", "category")
    if user.is_superuser or user_can_admin(user):
        return qs
    return qs.filter(Q(requester=user) | Q(assigned_to=user) | Q(department=user.area))


@login_required
def ticket_list(request):
    scope = request.GET.get("scope", "mine")
    status = request.GET.get("status", "")
    search = request.GET.get("q", "").strip()

    qs = Ticket.objects.select_related("requester", "assigned_to", "category")
    if not (request.user.is_superuser or user_can_admin(request.user)):
        if scope == "assigned":
            qs = qs.filter(assigned_to=request.user)
        elif scope == "all":
            qs = qs.filter(Q(requester=request.user) | Q(assigned_to=request.user) | Q(department=request.user.area))
        else:
            qs = qs.filter(requester=request.user)
    elif scope == "mine":
        qs = qs.filter(requester=request.user)
    elif scope == "assigned":
        qs = qs.filter(assigned_to=request.user)

    if status:
        qs = qs.filter(status=status)
    if search:
        search_q = Q(title__icontains=search) | Q(description__icontains=search)
        if search.isdigit():
            search_q |= Q(pk=int(search))
        qs = qs.filter(search_q)

    tabs = [
        ("mine", "Meus chamados"),
        ("assigned", "Meus chamados a tratar"),
    ]
    if request.user.is_superuser or user_can_admin(request.user):
        tabs.append(("all", "Todos os chamados"))

    return render(request, "tickets/list.html", {"tickets": qs, "tabs": tabs, "scope": scope, "status": status, "search": search})


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket.objects.select_related("requester", "assigned_to", "category"), pk=pk)
    if not user_can_view_ticket(request.user, ticket):
        return HttpResponseForbidden("Voce nao tem acesso a este chamado.")

    comment_form = TicketEventForm()
    status_form = TicketStatusForm()
    attachment_form = TicketAttachmentForm()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "comment":
            comment_form = TicketEventForm(request.POST)
            if comment_form.is_valid():
                TicketEvent.objects.create(
                    ticket=ticket,
                    actor=request.user,
                    kind="COMMENT",
                    message=comment_form.cleaned_data["message"],
                )
                messages.success(request, "Comentario adicionado.")
                return redirect("ticket_detail", pk=ticket.pk)

        elif action == "status":
            status_form = TicketStatusForm(request.POST)
            if status_form.is_valid():
                new_status = status_form.cleaned_data["status"]
                old_status = ticket.status
                can_change = user_can_edit_ticket(request.user, ticket)
                can_reopen = user_can_reopen_ticket(request.user, ticket)

                if new_status == "CLOSED" and not can_change:
                    messages.error(request, "Voce nao tem permissao para encerrar este chamado.")
                elif new_status == "DONE" and not (can_reopen or request.user.is_superuser):
                    messages.error(request, "Voce nao tem permissao para concluir este chamado.")
                elif new_status == "OPEN" and old_status == "CLOSED" and not can_reopen:
                    messages.error(request, "Voce nao tem permissao para reabrir este chamado.")
                else:
                    ticket.status = new_status
                    if new_status == "CLOSED":
                        ticket.closed_at = ticket.closed_at or ticket.last_status_change_at
                    elif new_status == "DONE":
                        ticket.concluded_at = ticket.concluded_at or ticket.last_status_change_at
                    elif new_status == "OPEN" and old_status == "CLOSED":
                        ticket.reopened_at = ticket.last_status_change_at
                        ticket.reopened_count += 1
                    ticket.save(update_fields=["status", "closed_at", "concluded_at", "reopened_at", "reopened_count", "last_status_change_at"])
                    TicketEvent.objects.create(
                        ticket=ticket,
                        actor=request.user,
                        kind="STATUS",
                        message=status_form.cleaned_data["message"] or f"Status alterado de {old_status} para {new_status}.",
                        from_status=old_status,
                        to_status=new_status,
                    )
                    if old_status == "CLOSED" and new_status == "OPEN":
                        TicketEvent.objects.create(
                            ticket=ticket,
                            actor=request.user,
                            kind="REOPEN",
                            message=status_form.cleaned_data["message"] or "Chamado reaberto.",
                            from_status=old_status,
                            to_status=new_status,
                        )
                    messages.success(request, "Status atualizado.")
                    return redirect("ticket_detail", pk=ticket.pk)

        elif action == "attachment":
            attachment_form = TicketAttachmentForm(request.POST, request.FILES)
            if attachment_form.is_valid():
                attachment = attachment_form.save(commit=False)
                attachment.ticket = ticket
                attachment.uploaded_by = request.user
                attachment.original_name = attachment.file.name.rsplit("/", 1)[-1]
                attachment.save()
                TicketEvent.objects.create(
                    ticket=ticket,
                    actor=request.user,
                    kind="COMMENT",
                    message=f"Anexo adicionado: {attachment.original_name}",
                )
                messages.success(request, "Anexo enviado.")
                return redirect("ticket_detail", pk=ticket.pk)

    return render(
        request,
        "tickets/detail.html",
        {
            "ticket": ticket,
            "comment_form": comment_form,
            "status_form": status_form,
            "attachment_form": attachment_form,
        },
    )


@login_required
def ticket_create(request):
    valid_departments = dict(Ticket._meta.get_field("department").choices)
    default_department = request.user.area if request.user.area in valid_departments else None
    form = TicketCreateForm(request.POST or None, request.FILES or None, default_department=default_department)
    if request.method == "POST" and form.is_valid():
        ticket = form.save(commit=False)
        ticket.requester = request.user
        ticket.save()
        TicketEvent.objects.create(
            ticket=ticket,
            actor=request.user,
            kind="COMMENT",
            message="Chamado aberto.",
        )
        initial_attachment = form.cleaned_data.get("initial_attachment")
        if initial_attachment:
            TicketAttachment.objects.create(
                ticket=ticket,
                uploaded_by=request.user,
                file=initial_attachment,
                original_name=initial_attachment.name,
            )
        messages.success(request, "Chamado criado com sucesso.")
        return redirect("ticket_detail", pk=ticket.pk)
    return render(request, "tickets/create.html", {"form": form})


def _admin_users_queryset(search=""):
    qs = User.objects.all().order_by("full_name", "matricula")
    if search:
        qs = qs.filter(Q(full_name__icontains=search) | Q(email__icontains=search) | Q(matricula__icontains=search))
    return qs


@login_required
@user_passes_test(user_can_admin)
def user_management(request):
    search = request.GET.get("q", "").strip()
    users = _admin_users_queryset(search)
    return render(request, "tickets/user_management.html", {"users": users, "search": search})


@login_required
@user_passes_test(user_can_admin)
def user_create(request):
    form = UserAdminForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, f"Usuario criado: {user.full_name}")
        return redirect("user_management")
    if request.method == "POST" and not form.is_valid():
        messages.error(request, "Nao foi possivel salvar o usuario. Verifique os campos informados.")
    return render(request, "tickets/user_form.html", {"form": form, "title": "Novo usuario"})


@login_required
@user_passes_test(user_can_admin)
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserUpdateForm(request.POST or None, instance=user)
    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        updated.is_staff = updated.cargo in {"TEC_INFORMATICA", "DIRETOR", "VICE_DIRETOR"}
        updated.save()
        messages.success(request, f"Usuario atualizado: {user.full_name}")
        return redirect("user_management")
    if request.method == "POST" and not form.is_valid():
        messages.error(request, "Nao foi possivel atualizar o usuario. Verifique os campos informados.")
    return render(request, "tickets/user_form.html", {"form": form, "title": f"Editar usuario: {user.full_name}"})


@login_required
@user_passes_test(user_can_admin)
def announcement_create(request):
    form = AnnouncementForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        announcement = form.save(commit=False)
        announcement.created_by = request.user
        announcement.save()
        uploaded_images = request.FILES.getlist("images")
        for index, uploaded_image in enumerate(uploaded_images):
            AnnouncementImage.objects.create(
                announcement=announcement,
                image=uploaded_image,
                sort_order=index,
            )
        messages.success(request, "Anuncio publicado.")
        return redirect("home")
    return render(request, "tickets/announcement_create.html", {"form": form})


def _announcements_queryset(search=""):
    qs = Announcement.objects.select_related("created_by").prefetch_related("announcement_images").order_by("-created_at")
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(body__icontains=search))
    return qs


@login_required
@user_passes_test(user_can_admin)
def announcement_management(request):
    search = request.GET.get("q", "").strip()
    announcements = [_announcement_gallery_payload(announcement) for announcement in _announcements_queryset(search)]
    return render(request, "tickets/announcement_management.html", {"announcements": announcements, "search": search})


@login_required
@user_passes_test(user_can_admin)
def announcement_edit(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    form = AnnouncementForm(request.POST or None, request.FILES or None, instance=announcement)
    if request.method == "POST" and form.is_valid():
        form.save()
        uploaded_images = request.FILES.getlist("images")
        start_index = announcement.announcement_images.count()
        for offset, uploaded_image in enumerate(uploaded_images):
            AnnouncementImage.objects.create(
                announcement=announcement,
                image=uploaded_image,
                sort_order=start_index + offset,
            )
        messages.success(request, "Anuncio atualizado.")
        return redirect("announcement_management")
    return render(
        request,
        "tickets/announcement_form.html",
        {
            "form": form,
            "title": "Editar anuncio",
            "announcement": announcement,
        },
    )


@login_required
@user_passes_test(user_can_admin)
def announcement_toggle_publish(request, pk):
    if request.method != "POST":
        return redirect("announcement_management")
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.is_published = not announcement.is_published
    announcement.save(update_fields=["is_published"])
    messages.success(
        request,
        "Anuncio publicado." if announcement.is_published else "Anuncio despublicado.",
    )
    return redirect("announcement_management")


@login_required
@user_passes_test(user_can_admin)
def announcement_delete(request, pk):
    if request.method != "POST":
        return redirect("announcement_management")
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.is_published = False
    announcement.save(update_fields=["is_published"])
    messages.success(request, "Anuncio desativado.")
    return redirect("announcement_management")


@login_required
def dashboard(request):
    visible = _visible_tickets_for(request.user)
    overdue_tickets = [ticket for ticket in visible if ticket.is_overdue]
    counts = {
        "open": visible.filter(status="OPEN").count(),
        "progress": visible.filter(status="IN_PROGRESS").count(),
        "closed": visible.filter(status="CLOSED").count(),
        "done": visible.filter(status="DONE").count(),
    }
    return render(
        request,
        "tickets/dashboard.html",
        {
            "counts": counts,
            "recent_tickets": visible[:8],
            "overdue_tickets": overdue_tickets[:8],
            "overdue_count": len(overdue_tickets),
        },
    )
