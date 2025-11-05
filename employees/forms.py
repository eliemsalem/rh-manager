from django import forms
from .models import Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = "__all__"  # allow editing of all fields

        widgets = {
            # --- Identity & Contact ---
            "prenom": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "First name"
            }),
            "nom": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Last name"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "name@example.com"
            }),
            "zoho_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Zoho ID"
            }),
            "country": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Country"
            }),
            "lead_1": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Team lead"
            }),

            # --- Job / Project ---
            "project": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Project name"
            }),
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Job title"
            }),

            # --- Contract ---
            "contract_type": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Contract type"
            }),
            "contract_company": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Contract company"
            }),
            "accomodation": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Accommodation details"
            }),

            # --- Dates ---
            "pt_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"},
                format="%Y-%m-%d"
            ),
            "ft_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"},
                format="%Y-%m-%d"
            ),
            "last_day": forms.DateInput(
                attrs={"type": "date", "class": "form-control"},
                format="%Y-%m-%d"
            ),
            "date_import": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M"
            ),

            # --- Salary ---
            "salaire_net": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Net salary"
            }),
            "devise": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Currency (e.g. EUR, USD)"
            }),

            # --- Bank info ---
            "bank_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Bank name"
            }),
            "bank_country": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Bank country"
            }),
            "iban": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "IBAN number"
            }),
            "swift": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "SWIFT / BIC code"
            }),

            # --- Other ---
            "comment": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Additional comments"
            }),

            # --- Active Switch ---
            "actif": forms.CheckboxInput(attrs={
                "class": "form-check-input",
                "role": "switch",
                "id": "id_actif"
            }),
        }

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    # ✅ Ajoute la vérification avant d'accéder au champ
    for field_name in ["pt_date", "ft_date", "last_day"]:
        if field_name in self.fields:
            self.fields[field_name].input_formats = ["%Y-%m-%d"]

    # ✅ Vérifie avant de toucher à date_import (sinon KeyError)
    if "date_import" in self.fields:
        self.fields["date_import"].input_formats = ["%Y-%m-%dT%H:%M"]

    # ✅ Bootstrap styling
    for name, field in self.fields.items():
        if name != "actif":
            css = field.widget.attrs.get("class", "")
            if "form-control" not in css:
                field.widget.attrs["class"] = f"{css} form-control".strip()

