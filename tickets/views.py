from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
import csv
import io
import json

from django.utils import timezone
from django.db import transaction

from .forms import (
    AnnouncementForm,
    LoginForm,
    UserAdminForm,
    UserUpdateForm,
    BulkUserUploadForm,
    TicketAttachmentForm,
    TicketAssignmentForm,
    TicketCreateForm,
    TicketEventForm,
    TicketStatusForm,
)
from .models import (
    Announcement,
    AnnouncementImage,
    CARGO_CHOICES_BY_DEPARTMENT,
    ChangeLog,
    area_for_department,
    Ticket,
    TicketAttachment,
    TicketEvent,
    TicketCategory,
    User,
    managed_departments_for_user,
    user_can_manage_ticket_responsible,
    user_can_admin,
    user_can_view_ticket,
)
from .services import assignable_users_for, format_responsible_change_message, format_ticket_status_message, ticket_status_choices_for
from .services_audit import serialize_announcement_for_audit, serialize_user_for_audit


def _announcement_gallery_payload(announcement):
    images = announcement.gallery_items
    return {
        "announcement": announcement,
        "images": images,
        "images_json": json.dumps(images),
        "image_count": len(images),
    }


def _log_change(entity_type, entity_id, action, actor, before_data=None, after_data=None):
    ChangeLog.objects.create(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor=actor,
        before_data=before_data or {},
        after_data=after_data or {},
    )


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
    department = request.GET.get("department", "").strip()

    if vinculo == "PROFESSOR":
        roles = [("HORISTA", "Professor Horista"), ("MENSALISTA", "Professor Mensalista")]
    elif vinculo == "ADMINISTRATIVO" and department:
        roles = list(CARGO_CHOICES_BY_DEPARTMENT.get(department, []))
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
    messages.success(request, "Você saiu do sistema.")
    return redirect("login")


def _visible_tickets_for(user, queryset=None):
    qs = queryset or Ticket.objects.select_related("requester", "assigned_to", "category")
    if user.is_superuser or user_can_admin(user):
        return qs
    managed_departments = managed_departments_for_user(user)
    visibility_q = Q(requester=user) | Q(assigned_to=user)
    if managed_departments:
        visibility_q |= Q(assigned_to__department__in=managed_departments) | Q(assigned_to__isnull=True, department__in=managed_departments)
    return qs.filter(visibility_q)


@login_required
def ticket_list(request):
    scope = request.GET.get("scope", "mine")
    status = request.GET.get("status", "")
    department = request.GET.get("department", "")
    search = request.GET.get("q", "").strip()
    managed_departments = managed_departments_for_user(request.user)
    can_see_all = bool(request.user.is_superuser or user_can_admin(request.user) or managed_departments)
    if scope == "all" and not can_see_all:
        scope = "mine"

    qs = Ticket.objects.select_related("requester", "assigned_to", "category")
    if not (request.user.is_superuser or user_can_admin(request.user)):
        if scope == "assigned":
            qs = qs.filter(assigned_to=request.user)
        elif scope == "all":
            qs = _visible_tickets_for(request.user, qs)
        else:
            qs = qs.filter(requester=request.user)
    elif scope == "mine":
        qs = qs.filter(requester=request.user)
    elif scope == "assigned":
        qs = qs.filter(assigned_to=request.user)

    if status:
        qs = qs.filter(status=status)
    if department:
        qs = qs.filter(Q(assigned_to__department=department) | Q(assigned_to__isnull=True, department=department))
    if search:
        search_q = Q(title__icontains=search) | Q(description__icontains=search)
        if search.isdigit():
            search_q |= Q(pk=int(search))
        qs = qs.filter(search_q)

    tabs = [
        ("mine", "Meus chamados"),
        ("assigned", "Meus chamados a tratar"),
    ]
    if can_see_all:
        tabs.append(("all", "Todos os chamados"))

    return render(request, "tickets/list.html", {"tickets": qs, "tabs": tabs, "scope": scope, "status": status, "department": department, "search": search})


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket.objects.select_related("requester", "assigned_to", "category"), pk=pk)
    if not user_can_view_ticket(request.user, ticket):
        return HttpResponseForbidden("Você não tem acesso a este chamado.")

    comment_form = TicketEventForm()
    status_form = TicketStatusForm(status_choices=ticket_status_choices_for(request.user, ticket))
    assignable_users = assignable_users_for(request.user, ticket)
    assignment_form = TicketAssignmentForm(queryset=assignable_users, initial={"assigned_to": ticket.assigned_to_id})
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
                messages.success(request, "Comentário adicionado.")
                return redirect("ticket_detail", pk=ticket.pk)

        elif action == "status":
            if request.POST.get("status") == ticket.status:
                messages.error(request, "O chamado já está neste status.")
                return redirect("ticket_detail", pk=ticket.pk)
            status_form = TicketStatusForm(request.POST, status_choices=ticket_status_choices_for(request.user, ticket))
            if status_form.is_valid():
                new_status = status_form.cleaned_data["status"]
                old_status = ticket.status
                target_department = status_form.cleaned_data.get("department") or ticket.department
                allowed_statuses = {value for value, _label in ticket_status_choices_for(request.user, ticket)}

                if new_status == old_status:
                    messages.error(request, "O chamado já está neste status.")
                elif old_status == "DONE":
                    messages.error(request, "Chamado concluído não pode receber nova alteração de status.")
                elif new_status not in allowed_statuses:
                    if new_status == "CLOSED":
                        messages.error(request, "Você não tem permissão para encerrar este chamado.")
                    elif new_status == "DONE":
                        messages.error(request, "Você não tem permissão para concluir este chamado.")
                    elif new_status == "OPEN":
                        messages.error(request, "Você não tem permissão para reabrir este chamado.")
                    else:
                        messages.error(request, "Você não tem permissão para alterar este chamado.")
                elif new_status == "FORWARDED" and not status_form.cleaned_data.get("department"):
                    messages.error(request, "Selecione o departamento de destino para encaminhar o chamado.")
                else:
                    comment_text = status_form.cleaned_data["message"].strip()
                    if comment_text:
                        TicketEvent.objects.create(
                            ticket=ticket,
                            actor=request.user,
                            kind="COMMENT",
                            message=comment_text,
                        )

                    if new_status == "FORWARDED":
                        ticket.assigned_to = None
                        ticket.area = area_for_department(target_department)
                        ticket.department = target_department
                    elif new_status == "IN_PROGRESS" and not ticket.assigned_to_id:
                        ticket.assigned_to = request.user
                        ticket.area = request.user.area
                        ticket.department = request.user.department
                    ticket.status = new_status
                    if new_status == "CLOSED":
                        ticket.closed_at = ticket.closed_at or timezone.now()
                    elif new_status == "DONE":
                        ticket.concluded_at = ticket.concluded_at or timezone.now()
                    elif new_status == "OPEN" and old_status == "CLOSED":
                        ticket.reopened_at = timezone.now()
                        ticket.reopened_count += 1
                    ticket.save(update_fields=["status", "assigned_to", "area", "department", "closed_at", "concluded_at", "reopened_at", "reopened_count", "last_status_change_at"])
                    TicketEvent.objects.create(
                        ticket=ticket,
                        actor=request.user,
                        kind="REOPEN" if old_status == "CLOSED" and new_status == "OPEN" else "STATUS",
                        message=format_ticket_status_message(ticket, old_status, new_status, request.user),
                        from_status=old_status,
                        to_status=new_status,
                    )
                    messages.success(request, "Status atualizado.")
                    return redirect("ticket_detail", pk=ticket.pk)
            else:
                messages.error(request, "Não foi possível atualizar o status. Verifique os campos informados.")

        elif action == "assignment":
            assignment_form = TicketAssignmentForm(request.POST, queryset=assignable_users_for(request.user, ticket))
            if assignment_form.is_valid():
                new_responsible = assignment_form.cleaned_data["assigned_to"]
                old_responsible = ticket.assigned_to
                if old_responsible and old_responsible.pk == new_responsible.pk:
                    messages.error(request, "Este usuário já é o responsável pelo chamado.")
                elif not user_can_manage_ticket_responsible(request.user, ticket):
                    messages.error(request, "Você não tem permissão para alterar o responsável deste chamado.")
                else:
                    ticket.assigned_to = new_responsible
                    ticket.area = new_responsible.area
                    ticket.department = new_responsible.department
                    ticket.save(update_fields=["assigned_to", "area", "department", "last_status_change_at"])
                    TicketEvent.objects.create(
                        ticket=ticket,
                        actor=request.user,
                        kind="TRANSFER",
                        message=format_responsible_change_message(ticket, old_responsible, new_responsible, request.user),
                    )
                    messages.success(request, "Responsável atualizado.")
                    return redirect("ticket_detail", pk=ticket.pk)
            else:
                messages.error(request, "Não foi possível atualizar o responsável.")

        elif action == "attachment":
            attachment_form = TicketAttachmentForm(request.POST, request.FILES)
            if attachment_form.is_valid():
                uploaded_files = attachment_form.cleaned_data.get("files", [])
                if not uploaded_files:
                    messages.error(request, "Selecione ao menos um anexo para enviar.")
                    return redirect("ticket_detail", pk=ticket.pk)
                attachment_names = []
                for uploaded_file in uploaded_files:
                    attachment = TicketAttachment.objects.create(
                        ticket=ticket,
                        uploaded_by=request.user,
                        file=uploaded_file,
                        original_name=uploaded_file.name,
                    )
                    attachment_names.append(attachment.original_name)
                TicketEvent.objects.create(
                    ticket=ticket,
                    actor=request.user,
                    kind="COMMENT",
                    message=f"Anexos adicionados: {', '.join(attachment_names)}.",
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
            "assignment_form": assignment_form,
            "can_manage_responsible": user_can_manage_ticket_responsible(request.user, ticket),
            "attachment_form": attachment_form,
        },
    )


@login_required
def ticket_create(request):
    default_area = request.user.area or None
    default_department = request.user.department or None
    form = TicketCreateForm(
        request.POST or None,
        request.FILES or None,
        default_area=default_area,
        default_department=default_department,
    )
    if request.method == "POST" and form.is_valid():
        ticket = form.save(commit=False)
        ticket.requester = request.user
        ticket.save()
        initial_files = form.cleaned_data.get("initial_attachment") or []
        attachment_names = []
        for uploaded_file in initial_files:
            attachment = TicketAttachment.objects.create(
                ticket=ticket,
                uploaded_by=request.user,
                file=uploaded_file,
                original_name=uploaded_file.name,
            )
            attachment_names.append(attachment.original_name)
        TicketEvent.objects.create(
            ticket=ticket,
            actor=request.user,
            kind="COMMENT",
            message="Chamado aberto." if not attachment_names else f"Chamado aberto com anexos iniciais: {', '.join(attachment_names)}.",
        )
        messages.success(request, "Chamado criado com sucesso.")
        return redirect("ticket_detail", pk=ticket.pk)
    return render(request, "tickets/create.html", {"form": form})


def _admin_users_queryset(search=""):
    qs = User.objects.all().order_by("full_name", "matricula")
    if search:
        qs = qs.filter(Q(full_name__icontains=search) | Q(email__icontains=search) | Q(matricula__icontains=search))
    return qs


USER_IMPORT_HEADERS = {
    "matricula": "matricula",
    "matrícula": "matricula",
    "nome": "full_name",
    "nome_completo": "full_name",
    "full_name": "full_name",
    "email": "email",
    "e-mail": "email",
    "vinculo": "vinculo",
    "vínculo": "vinculo",
    "area": "area",
    "área": "area",
    "departamento": "department",
    "department": "department",
    "cargo": "cargo",
    "senha": "password",
    "password": "password",
    "telefone": "phone",
    "phone": "phone",
    "ativo": "is_active",
    "is_active": "is_active",
}

USER_IMPORT_REQUIRED_FIELDS = ["matricula", "full_name", "email", "vinculo", "area", "department", "cargo", "password"]


def _normalize_header(header):
    return (header or "").strip().lower().replace(" ", "_")


def _decode_uploaded_text(uploaded_file):
    raw = uploaded_file.read()
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _detect_delimiter(sample):
    try:
        return csv.Sniffer().sniff(sample[:2048], delimiters=";,	,").delimiter
    except csv.Error:
        if ";" in sample:
            return ";"
        if "\t" in sample:
            return "\t"
        return ","


def _parse_bool(value):
    value = (value or "").strip().lower()
    if not value:
        return True
    if value in {"1", "sim", "s", "true", "ativo", "ativa"}:
        return True
    if value in {"0", "nao", "não", "n", "false", "inativo", "inativa"}:
        return False
    raise ValueError("Use sim/não, true/false ou 1/0.")


def _read_user_import_rows(uploaded_file):
    text = _decode_uploaded_text(uploaded_file)
    delimiter = _detect_delimiter(text)
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        return [], ["Arquivo sem cabeçalho."]

    normalized_headers = {}
    for header in reader.fieldnames:
        normalized = USER_IMPORT_HEADERS.get(_normalize_header(header))
        if normalized:
            normalized_headers[header] = normalized

    missing = [field for field in USER_IMPORT_REQUIRED_FIELDS if field not in normalized_headers.values()]
    if missing:
        return [], [f"Cabeçalho obrigatório ausente: {', '.join(missing)}."]

    rows = []
    errors = []
    seen_matriculas = set()
    seen_emails = set()

    for line_number, source_row in enumerate(reader, start=2):
        if not any((value or "").strip() for value in source_row.values()):
            continue
        row = {target: (source_row.get(source) or "").strip() for source, target in normalized_headers.items()}
        for field in USER_IMPORT_REQUIRED_FIELDS:
            if not row.get(field):
                errors.append(f"Linha {line_number}: campo obrigatório vazio ({field}).")

        matricula = row.get("matricula", "")
        email = row.get("email", "").lower()
        if matricula:
            if matricula in seen_matriculas:
                errors.append(f"Linha {line_number}: matrícula duplicada no arquivo ({matricula}).")
            seen_matriculas.add(matricula)
        if email:
            if email in seen_emails:
                errors.append(f"Linha {line_number}: e-mail duplicado no arquivo ({email}).")
            seen_emails.add(email)

        rows.append((line_number, row))

    if not rows:
        errors.append("Arquivo sem colaboradores para importar.")
    return rows, errors


def _validate_user_import_rows(rows):
    errors = []
    matriculas = [row["matricula"] for _line, row in rows if row.get("matricula")]
    emails = [row["email"] for _line, row in rows if row.get("email")]
    existing_matriculas = set(User.objects.filter(matricula__in=matriculas).values_list("matricula", flat=True))
    existing_emails = set(User.objects.filter(email__in=emails).values_list("email", flat=True))

    users_to_create = []
    for line_number, row in rows:
        if row.get("matricula") in existing_matriculas:
            errors.append(f"Linha {line_number}: já existe usuário com esta matrícula.")
        if row.get("email") in existing_emails:
            errors.append(f"Linha {line_number}: já existe usuário com este e-mail.")

        try:
            is_active = _parse_bool(row.get("is_active", "sim"))
        except ValueError as exc:
            errors.append(f"Linha {line_number}: campo ativo inválido. {exc}")
            is_active = True

        user = User(
            matricula=row.get("matricula", ""),
            email=row.get("email", ""),
            full_name=row.get("full_name", ""),
            vinculo=row.get("vinculo", ""),
            area=row.get("area", ""),
            department=row.get("department", ""),
            cargo=row.get("cargo", ""),
            phone=row.get("phone", ""),
            is_active=is_active,
        )
        try:
            user.full_clean()
        except Exception as exc:
            if hasattr(exc, "message_dict"):
                details = []
                for field_errors in exc.message_dict.values():
                    details.extend(field_errors)
                errors.append(f"Linha {line_number}: {'; '.join(details)}")
            else:
                errors.append(f"Linha {line_number}: {exc}")
        users_to_create.append((user, row["password"]))

    return users_to_create, errors


@login_required
@user_passes_test(user_can_admin)
def user_management(request):
    search = request.GET.get("q", "").strip()
    users = _admin_users_queryset(search)
    recent_changes = ChangeLog.objects.filter(entity_type="USER").select_related("actor").order_by("-created_at")[:10]
    return render(request, "tickets/user_management.html", {"users": users, "search": search, "recent_changes": recent_changes})


@login_required
@user_passes_test(user_can_admin)
def user_create(request):
    form = UserAdminForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        _log_change("USER", user.pk, "CREATE", request.user, after_data=serialize_user_for_audit(user))
        messages.success(request, f"Usuário criado: {user.full_name}")
        return redirect("user_management")
    if request.method == "POST" and not form.is_valid():
        messages.error(request, "Não foi possível salvar o usuário. Verifique os campos informados.")
    return render(request, "tickets/user_form.html", {"form": form, "title": "Novo usuário"})


@login_required
@user_passes_test(user_can_admin)
def user_bulk_upload(request):
    form = BulkUserUploadForm(request.POST or None, request.FILES or None)
    import_errors = []
    preview_count = 0
    if request.method == "POST" and form.is_valid():
        rows, import_errors = _read_user_import_rows(form.cleaned_data["file"])
        preview_count = len(rows)
        users_to_create, validation_errors = _validate_user_import_rows(rows) if not import_errors else ([], [])
        import_errors.extend(validation_errors)

        if not import_errors:
            with transaction.atomic():
                for user, password in users_to_create:
                    user.set_password(password)
                    user.save()
                    _log_change("USER", user.pk, "CREATE", request.user, after_data=serialize_user_for_audit(user))
            messages.success(request, f"{len(users_to_create)} colaborador(es) importado(s) com sucesso.")
            return redirect("user_management")

        messages.error(request, "Não foi possível importar os colaboradores. Corrija o arquivo e tente novamente.")
    elif request.method == "POST":
        messages.error(request, "Não foi possível ler o arquivo enviado.")

    return render(
        request,
        "tickets/user_bulk_upload.html",
        {
            "form": form,
            "import_errors": import_errors,
            "preview_count": preview_count,
        },
    )


@login_required
@user_passes_test(user_can_admin)
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserUpdateForm(request.POST or None, instance=user)
    if request.method == "POST" and form.is_valid():
        before_data = serialize_user_for_audit(user)
        updated = form.save(commit=False)
        updated.is_staff = updated.cargo in {"TEC_INFORMATICA", "DIRETOR", "VICE_DIRETOR"}
        updated.save()
        _log_change("USER", updated.pk, "UPDATE", request.user, before_data=before_data, after_data=serialize_user_for_audit(updated))
        messages.success(request, f"Usuário atualizado: {user.full_name}")
        return redirect("user_management")
    if request.method == "POST" and not form.is_valid():
        messages.error(request, "Não foi possível atualizar o usuário. Verifique os campos informados.")
    return render(request, "tickets/user_form.html", {"form": form, "title": f"Editar usuário: {user.full_name}"})


@login_required
@user_passes_test(user_can_admin)
def user_change_password(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = SetPasswordForm(user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        _log_change("USER", user.pk, "PASSWORD", request.user, after_data=serialize_user_for_audit(user))
        messages.success(request, "Senha alterada com sucesso.")
        return redirect("user_management")
    if request.method == "POST" and not form.is_valid():
        messages.error(request, "Não foi possível alterar a senha. Verifique os campos informados.")
    return render(request, "tickets/user_password_form.html", {"form": form, "title": f"Alterar senha: {user.full_name}"})


@login_required
@user_passes_test(user_can_admin)
def user_toggle_active(request, pk):
    if request.method != "POST":
        return redirect("user_management")
    user = get_object_or_404(User, pk=pk)
    before_data = serialize_user_for_audit(user)
    user.is_active = not user.is_active
    user.save(update_fields=["is_active", "is_staff"])
    _log_change(
        "USER",
        user.pk,
        "ACTIVATE" if user.is_active else "DEACTIVATE",
        request.user,
        before_data=before_data,
        after_data=serialize_user_for_audit(user),
    )
    messages.success(
        request,
        f"Usuário {'ativado' if user.is_active else 'inativado'} com sucesso.",
    )
    return redirect("user_management")


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
        _log_change("ANNOUNCEMENT", announcement.pk, "CREATE", request.user, after_data=serialize_announcement_for_audit(announcement))
        messages.success(request, "Anúncio publicado.")
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
    recent_changes = ChangeLog.objects.filter(entity_type="ANNOUNCEMENT").select_related("actor").order_by("-created_at")[:10]
    return render(request, "tickets/announcement_management.html", {"announcements": announcements, "search": search, "recent_changes": recent_changes})


@login_required
@user_passes_test(user_can_admin)
def announcement_edit(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    form = AnnouncementForm(request.POST or None, request.FILES or None, instance=announcement)
    if request.method == "POST" and form.is_valid():
        before_data = serialize_announcement_for_audit(announcement)
        form.save()
        uploaded_images = request.FILES.getlist("images")
        start_index = announcement.announcement_images.count()
        for offset, uploaded_image in enumerate(uploaded_images):
            AnnouncementImage.objects.create(
                announcement=announcement,
                image=uploaded_image,
                sort_order=start_index + offset,
            )
        _log_change("ANNOUNCEMENT", announcement.pk, "UPDATE", request.user, before_data=before_data, after_data=serialize_announcement_for_audit(announcement))
        messages.success(request, "Anúncio atualizado.")
        return redirect("announcement_management")
    return render(
        request,
        "tickets/announcement_form.html",
        {
            "form": form,
            "title": "Editar anúncio",
            "announcement": announcement,
        },
    )


@login_required
@user_passes_test(user_can_admin)
def announcement_toggle_publish(request, pk):
    if request.method != "POST":
        return redirect("announcement_management")
    announcement = get_object_or_404(Announcement, pk=pk)
    before_data = serialize_announcement_for_audit(announcement)
    announcement.is_published = not announcement.is_published
    announcement.save(update_fields=["is_published"])
    _log_change(
        "ANNOUNCEMENT",
        announcement.pk,
        "PUBLISH" if announcement.is_published else "UNPUBLISH",
        request.user,
        before_data=before_data,
        after_data=serialize_announcement_for_audit(announcement),
    )
    messages.success(
        request,
        "Anúncio publicado." if announcement.is_published else "Anúncio despublicado.",
    )
    return redirect("announcement_management")


@login_required
@user_passes_test(user_can_admin)
def announcement_delete(request, pk):
    if request.method != "POST":
        return redirect("announcement_management")
    announcement = get_object_or_404(Announcement, pk=pk)
    before_data = serialize_announcement_for_audit(announcement)
    announcement.is_published = False
    announcement.save(update_fields=["is_published"])
    _log_change("ANNOUNCEMENT", announcement.pk, "UNPUBLISH", request.user, before_data=before_data, after_data=serialize_announcement_for_audit(announcement))
    messages.success(request, "Anúncio despublicado.")
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
