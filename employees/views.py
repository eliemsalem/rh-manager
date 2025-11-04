import pandas as pd
from datetime import datetime
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Employee
from .forms import EmployeeForm


# -----------------------------
# 🔍 LIST & FILTERING
# -----------------------------
@login_required
def _filtered_queryset(request, include_inactive=False):
    """Return a filtered queryset of employees based on search text and active/inactive status."""
    q = request.GET.get("q", "").strip()
    qs = Employee.objects.all()

    if not include_inactive:
        qs = qs.filter(actif=True)

    if q:
        qs = qs.filter(
            Q(nom__icontains=q)
            | Q(prenom__icontains=q)
            | Q(project__icontains=q)
            | Q(country__icontains=q)
            | Q(bank_name__icontains=q)
            | Q(email__icontains=q)
            | Q(iban__icontains=q)
            | Q(swift__icontains=q)
        )
    return qs, q


@login_required
def employee_list(request):
    """Display a list of all active employees."""
    employees, q = _filtered_queryset(request, include_inactive=False)
    return render(request, "employees/list.html", {"employees": employees, "query": q})


@login_required
def employee_inactive_list(request):
    """Display a list of inactive employees."""
    employees, q = _filtered_queryset(request, include_inactive=True)
    employees = employees.filter(actif=False)
    return render(request, "employees/inactive_list.html", {"employees": employees, "query": q})


# -----------------------------
# 🧑‍💼 DETAIL / EDIT / ADD / DELETE
# -----------------------------
@login_required
def employee_detail(request, pk):
    """View or edit an employee profile."""
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f"{employee.prenom} {employee.nom} updated successfully ✅")
            return redirect("employees:employee_detail", pk=employee.pk)
        else:
            messages.error(request, "Please correct the highlighted errors.")
    else:
        form = EmployeeForm(instance=employee)
    return render(request, "employees/detail.html", {"employee": employee, "form": form})


@login_required
def employee_add(request):
    """Add a new employee record."""
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "New employee added successfully ✅")
            return redirect("employees:employee_list")
        else:
            messages.error(request, "Please correct the form errors before submitting.")
    else:
        form = EmployeeForm()
    return render(request, "employees/add.html", {"form": form})


@login_required
def employee_delete(request, pk):
    """Delete an employee record permanently."""
    emp = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        emp.delete()
        messages.success(request, f"{emp.prenom} {emp.nom} was deleted 🗑️")
        return redirect("employees:employee_list")
    return render(request, "employees/delete_confirm.html", {"employee": emp})


# -----------------------------
# 📥 EXCEL IMPORT UTILITIES
# -----------------------------
def clean_value(value):
    """Clean a text value: remove NaN/spaces and limit to 250 characters."""
    if pd.isna(value):
        return ""
    value = str(value).strip()
    return value[:250]


def safe_float(value):
    """Safely convert a value to float; return 0.0 if invalid."""
    try:
        if pd.isna(value) or value == "":
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def parse_date(value):
    """Parse an Excel or text date to YYYY-MM-DD."""
    if pd.isna(value) or not str(value).strip():
        return None
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.date()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return None


@login_required
def employee_import_excel(request):
    """Import employees from a formatted Excel file."""
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]

        # Validate file type
        if not file.name.lower().endswith(".xlsx"):
            messages.error(request, "Please upload a valid Excel file (.xlsx).")
            return redirect("employees:employee_import_excel")

        # Try reading Excel file
        try:
            df = pd.read_excel(file)
        except Exception as e:
            messages.error(request, f"Error reading Excel file: {e}")
            return redirect("employees:employee_import_excel")

        # Check required columns
        required_cols = {
            "Employee Name", "Zoho ID", "Project", "Title", "Email", "Country",
            "Lead 1", "PT Date", "FT Date", "Last day", "devise",
            "Salary", "Comment", "Accomodation",
            "Contract Type", "Contract company", "Bank Name", "Bank Country",
            "IBAN Number", "Swift"
        }
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            messages.error(request, f"Missing columns: {', '.join(missing_cols)}")
            return redirect("employees:employee_import_excel")

        added, updated, invalid_dates = 0, 0, 0

        # Process each row
        for _, row in df.iterrows():
            full_name = clean_value(row.get("Employee Name"))
            prenom, nom = "", ""
            if " " in full_name:
                parts = full_name.split(" ")
                prenom, nom = parts[0], " ".join(parts[1:])
            else:
                nom = full_name

            pt_date = parse_date(row.get("PT Date"))
            ft_date = parse_date(row.get("FT Date"))
            last_day = parse_date(row.get("Last day"))
            if row.get("PT Date") and not pt_date:
                invalid_dates += 1

            emp, created = Employee.objects.update_or_create(
                email=clean_value(row.get("Email")),
                defaults={
                    "prenom": prenom,
                    "nom": nom,
                    "project": clean_value(row.get("Project")),
                    "country": clean_value(row.get("Country")),
                    "bank_name": clean_value(row.get("Bank Name")),
                    "bank_country": clean_value(row.get("Bank Country")),
                    "iban": clean_value(row.get("IBAN Number")),
                    "swift": clean_value(row.get("Swift")),
                    "zoho_id": clean_value(row.get("Zoho ID")),
                    "contract_type": clean_value(row.get("Contract Type")),
                    "contract_company": clean_value(row.get("Contract company")),
                    "accomodation": clean_value(row.get("Accomodation")),
                    "comment": clean_value(row.get("Comment")),
                    "lead_1": clean_value(row.get("Lead 1")),
                    "title": clean_value(row.get("Title")),
                    "pt_date": pt_date,
                    "ft_date": ft_date,
                    "last_day": last_day,
                    "salaire_net": safe_float(row.get("Salary")),
                    "devise": clean_value(row.get("devise")),
                    "date_import": timezone.now(),
                    "actif": True,
                },
            )

            if created:
                added += 1
            else:
                updated += 1

        msg = f"{added} employees added, {updated} updated successfully ✅"
        if invalid_dates:
            msg += f" ({invalid_dates} invalid date formats ignored)"
        messages.success(request, msg)
        return redirect("employees:employee_list")

    return render(request, "employees/import.html")
import pandas as pd
from django.http import HttpResponse

@login_required
def download_template(request):
    """Provide a downloadable Excel template for employee import."""
    headers = [
        "Employee Name", "Zoho ID", "Project", "Title", "Email", "Country", "Lead 1",
        "PT Date", "FT Date", "Last day", "Salary", "devise", "Comment",
        "Accomodation", "Contract Type", "Contract company",
        "Bank Name", "Bank Country", "IBAN Number", "Swift"
    ]

    df = pd.DataFrame(columns=headers)

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="employee_import_template.xlsx"'
    df.to_excel(response, index=False)
    return response
