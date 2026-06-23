from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import (
    AREA_CHOICES,
    CARGO_CHOICES_BY_AREA,
    Announcement,
    Ticket,
    TicketAttachment,
    TicketCategory,
    TicketEvent,
    User,
)


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Matricula ou e-mail", widget=forms.TextInput(attrs={"placeholder": "Matricula ou e-mail"}))
    password = forms.CharField(label="Senha", widget=forms.PasswordInput(attrs={"placeholder": "Senha"}))


def all_admin_cargos():
    cargos = []
    for area_code, choices in CARGO_CHOICES_BY_AREA.items():
        if area_code == "DOCENCIA":
            continue
        cargos.extend(choices)
    return cargos


def admin_area_choices():
    return [choice for choice in AREA_CHOICES if choice[0] != "DOCENCIA"]


class UserCreateForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        vinculo = None
        area = None
        if self.data:
            vinculo = self.data.get("vinculo") or None
            area = self.data.get("area") or None
        elif self.instance and self.instance.pk:
            vinculo = self.instance.vinculo
            area = self.instance.area or None

        self.fields["vinculo"].choices = [("", "Selecione o vinculo")] + list(User._meta.get_field("vinculo").choices)
        self.fields["area"].choices = [("", "Selecione a area")] + (AREA_CHOICES if vinculo != "ADMINISTRATIVO" else admin_area_choices())
        self.fields["cargo"].choices = self._cargo_choices_for(vinculo, area)

        if vinculo == "PROFESSOR":
            self.fields["area"].initial = "DOCENCIA"
            self.fields["area"].disabled = True
        elif vinculo == "ADMINISTRATIVO" and area not in dict(admin_area_choices()):
            self.fields["area"].initial = ""

    def _cargo_choices_for(self, vinculo, area):
        if vinculo == "PROFESSOR":
            return [("", "Selecione o cargo")] + list(CARGO_CHOICES_BY_AREA["DOCENCIA"])
        if area in CARGO_CHOICES_BY_AREA:
            return [("", "Selecione o cargo")] + list(CARGO_CHOICES_BY_AREA[area])
        return [("", "Selecione o cargo")] + all_admin_cargos()

    def clean(self):
        cleaned = super().clean()
        vinculo = cleaned.get("vinculo")
        area = cleaned.get("area")
        cargo = cleaned.get("cargo")

        if vinculo == "PROFESSOR":
            cleaned["area"] = "DOCENCIA"
            if cargo not in {"HORISTA", "MENSALISTA"}:
                raise forms.ValidationError({"cargo": "Professor deve ser Horista ou Mensalista."})
        elif vinculo == "ADMINISTRATIVO":
            if not area:
                raise forms.ValidationError({"area": "Informe a area do funcionario administrativo."})
            if area == "DOCENCIA":
                raise forms.ValidationError({"area": "Docencia e exclusiva para professores."})
            allowed = {code for code, _label in CARGO_CHOICES_BY_AREA.get(area, [])}
            if cargo not in allowed:
                raise forms.ValidationError({"cargo": "Cargo invalido para a area selecionada."})
        else:
            raise forms.ValidationError({"vinculo": "Selecione um vinculo valido."})

        return cleaned

    class Meta:
        model = User
        fields = ["full_name", "email", "matricula", "vinculo", "area", "cargo"]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Nome completo"}),
            "email": forms.EmailInput(attrs={"placeholder": "E-mail institucional"}),
            "matricula": forms.TextInput(attrs={"placeholder": "Matricula"}),
        }


class UserAdminForm(UserCreateForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = user.cargo in {"TEC_INFORMATICA", "DIRETOR", "VICE_DIRETOR"}
        if commit:
            user.save()
            self.save_m2m()
        return user


class UserUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        vinculo = None
        area = None
        if self.data:
            vinculo = self.data.get("vinculo") or None
            area = self.data.get("area") or None
        elif self.instance and self.instance.pk:
            vinculo = self.instance.vinculo
            area = self.instance.area or None

        self.fields["vinculo"].choices = [("", "Selecione o vinculo")] + list(User._meta.get_field("vinculo").choices)
        self.fields["area"].choices = [("", "Selecione a area")] + (AREA_CHOICES if vinculo != "ADMINISTRATIVO" else admin_area_choices())
        self.fields["cargo"].choices = self._cargo_choices_for(vinculo, area)

        if vinculo == "PROFESSOR":
            self.fields["area"].initial = "DOCENCIA"
            self.fields["area"].disabled = True

    def _cargo_choices_for(self, vinculo, area):
        if vinculo == "PROFESSOR":
            return [("", "Selecione o cargo")] + list(CARGO_CHOICES_BY_AREA["DOCENCIA"])
        if area in CARGO_CHOICES_BY_AREA:
            return [("", "Selecione o cargo")] + list(CARGO_CHOICES_BY_AREA[area])
        return [("", "Selecione o cargo")] + all_admin_cargos()

    def clean(self):
        cleaned = super().clean()
        vinculo = cleaned.get("vinculo")
        area = cleaned.get("area")
        cargo = cleaned.get("cargo")

        if vinculo == "PROFESSOR":
            cleaned["area"] = "DOCENCIA"
            if cargo not in {"HORISTA", "MENSALISTA"}:
                raise forms.ValidationError({"cargo": "Professor deve ser Horista ou Mensalista."})
        elif vinculo == "ADMINISTRATIVO":
            if not area:
                raise forms.ValidationError({"area": "Informe a area do funcionario administrativo."})
            if area == "DOCENCIA":
                raise forms.ValidationError({"area": "Docencia e exclusiva para professores."})
            allowed = {code for code, _label in CARGO_CHOICES_BY_AREA.get(area, [])}
            if cargo not in allowed:
                raise forms.ValidationError({"cargo": "Cargo invalido para a area selecionada."})
        else:
            raise forms.ValidationError({"vinculo": "Selecione um vinculo valido."})

        return cleaned

    class Meta:
        model = User
        fields = ["full_name", "email", "matricula", "vinculo", "area", "cargo"]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Nome completo"}),
            "email": forms.EmailInput(attrs={"placeholder": "E-mail institucional"}),
            "matricula": forms.TextInput(attrs={"placeholder": "Matricula"}),
        }


class TicketCreateForm(forms.ModelForm):
    initial_attachment = forms.FileField(required=False, label="Anexo inicial")

    class Meta:
        model = Ticket
        fields = ["department", "category", "title", "description", "urgency"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Assunto resumido"}),
            "description": forms.Textarea(attrs={"rows": 6, "placeholder": "Descreva a demanda com o maximo de detalhes"}),
        }

    def __init__(self, *args, **kwargs):
        default_department = kwargs.pop("default_department", None)
        super().__init__(*args, **kwargs)

        selected_department = None
        if self.data:
            selected_department = self.data.get("department") or None
        elif default_department:
            selected_department = default_department
            self.fields["department"].initial = default_department

        if selected_department:
            self.fields["category"].queryset = TicketCategory.objects.filter(department=selected_department, is_active=True)
        else:
            self.fields["category"].queryset = TicketCategory.objects.filter(is_active=True)
        self.fields["category"].required = False


class TicketEventForm(forms.ModelForm):
    class Meta:
        model = TicketEvent
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4, "placeholder": "Escreva um comentario ou tratativa"}),
        }


class TicketStatusForm(forms.Form):
    status = forms.ChoiceField(choices=[("", "Selecionar status")] + Ticket._meta.get_field("status").choices)
    message = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Motivo da mudanca"}))


class TicketAttachmentForm(forms.ModelForm):
    class Meta:
        model = TicketAttachment
        fields = ["file"]


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "body", "is_published"]
        widgets = {
            "body": forms.Textarea(attrs={"class": "rich-editor__hidden"}),
        }
