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

            # --- Job / Project ---
            "project": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Project name"
            }),
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Job title"
            }),
            "lead_1": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Team lead"
            }),
            "accomodation": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Accommodation details"
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

            # --- Salary ---
            "salaire_net": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Net salary"
            }),
            "devise": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Currency (e.g. EUR, USD)"
            }),

            # --- Dates ---
            "pt_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),
            "ft_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),
            "last_day": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),

            # --- Other ---
            "country": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Country"
            }),
            "zoho_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Zoho ID"
            }),
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
        # ✅ Apply Bootstrap styling to all fields except the "Active" checkbox
        for name, field in self.fields.items():
            if name != "actif":
                css = field.widget.attrs.get("class", "")
                if "form-control" not in css:
                    field.widget.attrs["class"] = f"{css} form-control".strip()
