from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Announcement, ChangeLog, Ticket, TicketAttachment, TicketCategory, TicketEvent, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("matricula", "full_name", "email", "vinculo", "area", "department", "cargo", "is_staff")
    search_fields = ("matricula", "full_name", "email")
    ordering = ("full_name",)
    fieldsets = (
        (None, {"fields": ("matricula", "email", "password")}),
        ("Dados pessoais", {"fields": ("full_name", "vinculo", "area", "department", "cargo", "phone")}),
        ("Permissoes", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Datas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("matricula", "email", "full_name", "vinculo", "area", "department", "cargo", "password1", "password2"),
        }),
    )


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ("department", "name", "is_active")
    list_filter = ("department", "is_active")
    search_fields = ("name", "description")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "area", "department", "status", "requester", "assigned_to", "opened_at")
    list_filter = ("area", "department", "status", "urgency")
    search_fields = ("title", "description")
    autocomplete_fields = ("requester", "assigned_to", "category")


@admin.register(TicketEvent)
class TicketEventAdmin(admin.ModelAdmin):
    list_display = ("ticket", "kind", "actor", "created_at")
    list_filter = ("kind", "created_at")
    search_fields = ("message",)


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "original_name", "uploaded_by", "created_at")
    search_fields = ("original_name",)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "created_by", "created_at")
    list_filter = ("is_published",)
    search_fields = ("title", "body")


@admin.register(ChangeLog)
class ChangeLogAdmin(admin.ModelAdmin):
    list_display = ("entity_type", "entity_id", "action", "actor", "created_at")
    list_filter = ("entity_type", "action", "created_at")
    search_fields = ("entity_type", "entity_id")
