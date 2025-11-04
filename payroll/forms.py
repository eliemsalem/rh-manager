from django import forms
from datetime import date
from .models import Payroll

# --- Dropdown choices ---
MONTHS = [
    (1, "January"), (2, "February"), (3, "March"), (4, "April"),
    (5, "May"), (6, "June"), (7, "July"), (8, "August"),
    (9, "September"), (10, "October"), (11, "November"), (12, "December"),
]

YEARS = [(y, str(y)) for y in range(2020, date.today().year + 3)]


class PayrollForm(forms.ModelForm):
    # Replace "periode" field with Month / Year dropdowns
    month = forms.ChoiceField(choices=MONTHS, label="Month")
    year = forms.ChoiceField(choices=YEARS, label="Year")

    class Meta:
        model = Payroll
        exclude = ("periode",)
        widgets = {
            "employee": forms.Select(attrs={"class": "form-select"}),
            "salaire_base": forms.NumberInput(attrs={"class": "form-control"}),
            "heures_supp": forms.NumberInput(attrs={"class": "form-control"}),
            "montant_heures_supp": forms.NumberInput(attrs={"class": "form-control"}),
            "remboursement": forms.NumberInput(attrs={"class": "form-control"}),
            "remboursement_comment": forms.TextInput(attrs={"class": "form-control"}),
            "autres": forms.NumberInput(attrs={"class": "form-control"}),
            "autres_comment": forms.TextInput(attrs={"class": "form-control"}),
            "deduction": forms.NumberInput(attrs={"class": "form-control"}),
            "nb_conges": forms.NumberInput(attrs={"class": "form-control"}),
            "total_paye": forms.NumberInput(attrs={"class": "form-control"}),
            "devise": forms.TextInput(attrs={"class": "form-control"}),
        }

        # ✅ Translated labels
        labels = {
            "employee": "Employee",
            "salaire_base": "Base Salary",
            "heures_supp": "Overtime Hours",
            "montant_heures_supp": "Overtime Amount",
            "remboursement": "Reimbursement",
            "remboursement_comment": "Reimbursement Comment",
            "autres": "Other Amounts",
            "autres_comment": "Other Comments",
            "deduction": "Deduction",
            "nb_conges": "Vacation Days",
            "total_paye": "Total Pay",
            "devise": "Currency",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Auto-fill month and year from existing payroll period
        if self.instance and self.instance.periode:
            self.fields["month"].initial = self.instance.periode.month
            self.fields["year"].initial = self.instance.periode.year
        else:
            today = date.today()
            self.fields["month"].initial = today.month
            self.fields["year"].initial = today.year

    def save(self, commit=True):
        obj = super().save(commit=False)
        month = int(self.cleaned_data["month"])
        year = int(self.cleaned_data["year"])
        obj.periode = date(year, month, 1)  # store first day of month
        if commit:
            obj.save()
        return obj
