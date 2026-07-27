from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import (
    AREA_CHOICES,
    CARGO_CHOICES_BY_DEPARTMENT,
    DEPARTMENT_CHOICES,
    DEPARTMENTS_BY_AREA,
    Announcement,
    Ticket,
    TicketCategory,
    TicketEvent,
    User,
    cargos_for_department,
)


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Matricula ou e-mail", widget=forms.TextInput(attrs={"placeholder": "Matricula ou e-mail"}))
    password = forms.CharField(label="Senha", widget=forms.PasswordInput(attrs={"placeholder": "Senha"}))


def all_admin_cargos():
    cargos = []
    for department_code, choices in CARGO_CHOICES_BY_DEPARTMENT.items():
        if department_code == "DOCENCIA":
            continue
        cargos.extend(choices)
    return cargos


def admin_area_choices():
    return list(AREA_CHOICES)


def department_choices_for_area(area):
    return [("", "Selecione o departamento")] + list(DEPARTMENTS_BY_AREA.get(area, []))


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if data in (None, "", []):
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        cleaned = []
        errors = []
        for item in data:
            try:
                cleaned.append(super().clean(item, initial))
            except forms.ValidationError as exc:
                errors.extend(exc.error_list)
        if errors:
            raise forms.ValidationError(errors)
        return cleaned


class UserCreateForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        vinculo = None
        area = None
        department = None
        if self.data:
            vinculo = self.data.get("vinculo") or None
            area = self.data.get("area") or None
            department = self.data.get("department") or None
        elif self.instance and self.instance.pk:
            vinculo = self.instance.vinculo
            area = self.instance.area or None
            department = self.instance.department or None

        self.fields["vinculo"].choices = [("", "Selecione o vinculo")] + list(User._meta.get_field("vinculo").choices)
        self.fields["area"].choices = [("", "Selecione a area")] + admin_area_choices()
        self.fields["area"].required = True
        self.fields["department"].required = True
        self.fields["cargo"].required = True
        if vinculo == "PROFESSOR":
            self.fields["department"].choices = [("DOCENCIA", "Docencia")]
        else:
            self.fields["department"].choices = department_choices_for_area(area) if area else [("", "Selecione o departamento")]
        self.fields["cargo"].choices = self._cargo_choices_for(vinculo, department)

        if vinculo == "PROFESSOR":
            self.fields["area"].initial = "COORDENACAO_PEDAGOGICA"
            self.fields["area"].disabled = True
            self.fields["department"].initial = "DOCENCIA"
            self.fields["department"].disabled = True
        elif vinculo == "ADMINISTRATIVO" and area not in dict(admin_area_choices()):
            self.fields["area"].initial = ""

    def _cargo_choices_for(self, vinculo, department):
        if vinculo == "PROFESSOR":
            return cargos_for_department("DOCENCIA")
        if department in CARGO_CHOICES_BY_DEPARTMENT:
            return cargos_for_department(department)
        return [("", "Selecione o cargo")] + all_admin_cargos()

    def clean(self):
        cleaned = super().clean()
        vinculo = cleaned.get("vinculo")
        area = cleaned.get("area")
        department = cleaned.get("department")
        cargo = cleaned.get("cargo")

        if vinculo == "PROFESSOR":
            cleaned["area"] = "COORDENACAO_PEDAGOGICA"
            cleaned["department"] = "DOCENCIA"
            if cargo not in {"HORISTA", "MENSALISTA"}:
                raise forms.ValidationError({"cargo": "Professor deve ser Horista ou Mensalista."})
        elif vinculo == "ADMINISTRATIVO":
            if not area:
                raise forms.ValidationError({"area": "Informe a area do funcionario administrativo."})
            if not department:
                raise forms.ValidationError({"department": "Informe o departamento do funcionario administrativo."})
            allowed_departments = {code for code, _label in DEPARTMENTS_BY_AREA.get(area, [])}
            if department not in allowed_departments:
                raise forms.ValidationError({"department": "Departamento invalido para a area selecionada."})
            allowed = {code for code, _label in CARGO_CHOICES_BY_DEPARTMENT.get(department, [])}
            if cargo not in allowed:
                raise forms.ValidationError({"cargo": "Cargo invalido para o departamento selecionado."})
        else:
            raise forms.ValidationError({"vinculo": "Selecione um vinculo valido."})

        return cleaned

    class Meta:
        model = User
        fields = ["full_name", "email", "matricula", "vinculo", "area", "department", "cargo"]
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
        department = None
        if self.data:
            vinculo = self.data.get("vinculo") or None
            area = self.data.get("area") or None
            department = self.data.get("department") or None
        elif self.instance and self.instance.pk:
            vinculo = self.instance.vinculo
            area = self.instance.area or None
            department = self.instance.department or None

        self.fields["vinculo"].choices = [("", "Selecione o vinculo")] + list(User._meta.get_field("vinculo").choices)
        self.fields["area"].choices = [("", "Selecione a area")] + admin_area_choices()
        self.fields["area"].required = True
        self.fields["department"].required = True
        self.fields["cargo"].required = True
        if vinculo == "PROFESSOR":
            self.fields["department"].choices = [("DOCENCIA", "Docencia")]
        else:
            self.fields["department"].choices = department_choices_for_area(area) if area else [("", "Selecione o departamento")]
        self.fields["cargo"].choices = self._cargo_choices_for(vinculo, department)

        if vinculo == "PROFESSOR":
            self.fields["area"].initial = "COORDENACAO_PEDAGOGICA"
            self.fields["area"].disabled = True
            self.fields["department"].initial = "DOCENCIA"
            self.fields["department"].disabled = True

    def _cargo_choices_for(self, vinculo, department):
        if vinculo == "PROFESSOR":
            return cargos_for_department("DOCENCIA")
        if department in CARGO_CHOICES_BY_DEPARTMENT:
            return cargos_for_department(department)
        return [("", "Selecione o cargo")] + all_admin_cargos()

    def clean(self):
        cleaned = super().clean()
        vinculo = cleaned.get("vinculo")
        area = cleaned.get("area")
        department = cleaned.get("department")
        cargo = cleaned.get("cargo")

        if vinculo == "PROFESSOR":
            cleaned["area"] = "COORDENACAO_PEDAGOGICA"
            cleaned["department"] = "DOCENCIA"
            if cargo not in {"HORISTA", "MENSALISTA"}:
                raise forms.ValidationError({"cargo": "Professor deve ser Horista ou Mensalista."})
        elif vinculo == "ADMINISTRATIVO":
            if not area:
                raise forms.ValidationError({"area": "Informe a area do funcionario administrativo."})
            if not department:
                raise forms.ValidationError({"department": "Informe o departamento do funcionario administrativo."})
            allowed_departments = {code for code, _label in DEPARTMENTS_BY_AREA.get(area, [])}
            if department not in allowed_departments:
                raise forms.ValidationError({"department": "Departamento invalido para a area selecionada."})
            allowed = {code for code, _label in CARGO_CHOICES_BY_DEPARTMENT.get(department, [])}
            if cargo not in allowed:
                raise forms.ValidationError({"cargo": "Cargo invalido para o departamento selecionado."})
        else:
            raise forms.ValidationError({"vinculo": "Selecione um vinculo valido."})

        return cleaned

    class Meta:
        model = User
        fields = ["full_name", "email", "matricula", "vinculo", "area", "department", "cargo"]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Nome completo"}),
            "email": forms.EmailInput(attrs={"placeholder": "E-mail institucional"}),
            "matricula": forms.TextInput(attrs={"placeholder": "Matricula"}),
        }


class TicketCreateForm(forms.ModelForm):
    initial_attachment = MultipleFileField(required=False, label="Anexos iniciais")

    class Meta:
        model = Ticket
        fields = ["area", "department", "category", "title", "description", "urgency"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Assunto resumido"}),
            "description": forms.Textarea(attrs={"rows": 6, "placeholder": "Descreva a demanda com o maximo de detalhes"}),
        }

    def __init__(self, *args, **kwargs):
        default_area = kwargs.pop("default_area", None)
        default_department = kwargs.pop("default_department", None)
        super().__init__(*args, **kwargs)
        self.fields["area"].required = True
        self.fields["department"].required = True

        selected_area = None
        selected_department = None
        if self.data:
            selected_area = self.data.get("area") or None
            selected_department = self.data.get("department") or None
        elif default_area:
            selected_area = default_area
            self.fields["area"].initial = default_area
            if default_department:
                selected_department = default_department
                self.fields["department"].initial = default_department

        if selected_area:
            self.fields["department"].choices = [("", "Selecione o departamento")] + list(DEPARTMENTS_BY_AREA.get(selected_area, []))
        else:
            self.fields["department"].choices = [("", "Selecione o departamento")] + list(DEPARTMENT_CHOICES)

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
    department = forms.ChoiceField(choices=[("", "Selecionar departamento")] + DEPARTMENT_CHOICES, required=False)
    message = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Motivo da mudanca"}))

    def __init__(self, *args, **kwargs):
        status_choices = kwargs.pop("status_choices", None)
        super().__init__(*args, **kwargs)
        if status_choices is not None:
            self.fields["status"].choices = [("", "Selecionar status")] + list(status_choices)

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        department = cleaned.get("department")
        if status == "FORWARDED" and not department:
            raise forms.ValidationError({"department": "Selecione o departamento de destino para encaminhar o chamado."})
        return cleaned


class TicketAssignmentForm(forms.Form):
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        empty_label="Selecionar responsavel",
        label="Responsavel",
    )

    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop("queryset", User.objects.none())
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = queryset


class TicketAttachmentForm(forms.Form):
    files = MultipleFileField(required=False, label="Anexos")


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "body", "is_published"]
        widgets = {
            "body": forms.Textarea(attrs={"class": "rich-editor__hidden"}),
        }
