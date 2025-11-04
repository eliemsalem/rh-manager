from datetime import date
from calendar import monthrange
import os, io, zipfile
import pandas as pd
from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from employees.models import Employee
from .models import Payroll
from .forms import PayrollForm
from .utils.pdf_generator import generate_paie_pdf


# -----------------------------
# 🔧 HELPERS
# -----------------------------
def _year_month_from_request(request):
    try:
        y = int(request.GET.get("year") or date.today().year)
        m = int(request.GET.get("month") or date.today().month)
    except Exception:
        y, m = date.today().year, date.today().month
    return y, m


def _periode_date(y, m):
    return date(y, m, 1)


def _media_month_folder(y, m):
    base = getattr(settings, "MEDIA_ROOT", os.path.join(settings.BASE_DIR, "media"))
    folder = os.path.join(base, "payroll", f"{y:04d}-{m:02d}")
    os.makedirs(folder, exist_ok=True)
    return folder


# -----------------------------
# 📄 PAYROLL LIST
# -----------------------------
@login_required
def payroll_list(request):
    """Display payroll list for a given month."""
    year, month = _year_month_from_request(request)
    periode = _periode_date(year, month)

    q = (request.GET.get("q") or "").strip()
    qs = Payroll.objects.filter(periode=periode).select_related("employee")
    if q:
        qs = qs.filter(
            Q(employee__nom__icontains=q)
            | Q(employee__prenom__icontains=q)
            | Q(employee__email__icontains=q)
            | Q(employee__project__icontains=q)
        )

    months = [(i, date(2000, i, 1).strftime("%B")) for i in range(1, 13)]
    years = list(range(date.today().year - 5, date.today().year + 2))

    return render(
        request,
        "payroll/list.html",
        {
            "items": qs.order_by("employee__nom", "employee__prenom"),
            "year": year,
            "month": month,
            "months": months,
            "years": years,
            "query": q,
        },
    )


# -----------------------------
# ✏️ EDIT PAYROLL
# -----------------------------
@login_required
def payroll_edit(request, pk):
    """Edit a payroll entry."""
    obj = get_object_or_404(Payroll, pk=pk)
    if request.method == "POST":
        form = PayrollForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"Payroll for {obj.employee.prenom} {obj.employee.nom} updated ✅")
            return redirect("payroll:payroll_list")
        else:
            messages.error(request, "Please correct the form errors.")
    else:
        form = PayrollForm(instance=obj)
    return render(request, "payroll/edit.html", {"form": form, "payroll": obj})


# -----------------------------
# 🧾 GENERATE MONTHLY PAYROLLS
# -----------------------------



from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect

from employees.models import Employee
from .models import Payroll

# Si ces helpers n'existent pas chez toi, voir + bas pour des versions locales
from datetime import date
import os
from django.conf import settings

@login_required
# --- Helpers locaux pour les périodes et le stockage ---
def _year_month_from_request(request):
    """Extrait l'année et le mois depuis les paramètres GET, ou utilise la date du jour."""
    today = date.today()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
    except ValueError:
        year, month = today.year, today.month
    return year, month


def _periode_date(year, month):
    """Retourne un objet date correspondant au 1er jour du mois donné."""
    return date(year, month, 1)


def _media_month_folder(year, month):
    """Crée automatiquement un dossier media/payroll/YYYY_MM/ si inexistant."""
    folder_name = f"{year}_{str(month).zfill(2)}"
    folder_path = os.path.join(settings.MEDIA_ROOT, "payroll", folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


@login_required
def generate_month_for_actives(request):
    """
    Crée ou met à jour les paies POUR LES EMPLOYÉS ACTIFS uniquement.
    Supprime automatiquement les paies du mois pour les inactifs.
    Vérifie la cohérence et crée le dossier média du mois.
    """

    # --- Période (sécurisée) ---
    try:
        year, month = _year_month_from_request(request)
    except Exception:
        today = date.today()
        y = request.GET.get("year")
        m = request.GET.get("month")
        year = int(y) if y and y.isdigit() else today.year
        month = int(m) if m and m.isdigit() else today.month

    try:
        periode = _periode_date(year, month)
    except Exception:
        periode = date(year, month, 1)

    created = updated = deleted = 0

    # --- Employés actifs uniquement ---
    actifs_qs = Employee.objects.filter(actif=True).only(
        "id", "actif", "prenom", "nom", "email"
    )
    actifs_ids = list(actifs_qs.values_list("id", flat=True))

    # --- Employés inactifs (pour suppression) ---
    inactifs_ids = list(Employee.objects.filter(actif=False).values_list("id", flat=True))

    # --- Helpers internes ---
    def _emp_salary(emp):
        return (
            getattr(emp, "salaire_net", None)
            or getattr(emp, "salaire_base", None)
            or 0
        )

    def _emp_currency(emp):
        return getattr(emp, "devise", None) or "EUR"

    with transaction.atomic():
        # 1️⃣ Supprimer les paies des inactifs pour ce mois
        deleted, _ = Payroll.objects.filter(
            periode=periode, employee_id__in=inactifs_ids
        ).delete()

        # 2️⃣ Créer / mettre à jour pour les actifs
        for emp in actifs_qs:
            defaults = {
                "salaire_base": _emp_salary(emp),
                "devise": _emp_currency(emp),
            }
            payroll, was_created = Payroll.objects.update_or_create(
                employee=emp,
                periode=periode,
                defaults=defaults,
            )
            created += int(was_created)
            updated += int(not was_created)

        # 3️⃣ Vérifier cohérence
        have_payroll_ids = set(
            Payroll.objects.filter(periode=periode).values_list("employee_id", flat=True)
        )
        missing_ids = set(actifs_ids) - have_payroll_ids
        orphaned_count = Payroll.objects.filter(
            periode=periode, employee_id__in=inactifs_ids
        ).count()

    # --- 📁 Création du dossier média du mois (hors transaction) ---
    try:
        folder = os.path.join(settings.MEDIA_ROOT, "payroll", f"{year}_{month:02d}")
        os.makedirs(folder, exist_ok=True)
    except Exception:
        pass

    # --- 🧾 Messages finaux ---
    base_msg = f"✅ {created} créées, {updated} mises à jour pour {periode:%m/%Y}."
    info_parts = []
    if deleted:
        info_parts.append(f"🧹 {deleted} paie(s) supprimée(s) (inactifs).")
    if missing_ids:
        info_parts.append(f"⚠️ {len(missing_ids)} employé(s) actif(s) sans paie.")
    if orphaned_count:
        info_parts.append(f"❌ {orphaned_count} paie(s) orpheline(s) détectée(s).")

    if info_parts:
        messages.warning(request, base_msg + " " + " ".join(info_parts))
    else:
        messages.success(request, base_msg + " Cohérence OK ✅")

    return redirect(f"/payroll/?year={year}&month={month}")




# -----------------------------
# 📄 SINGLE PDF GENERATION
# -----------------------------
@login_required
def payroll_pdf(request, pk):
    """Generate a professional payroll PDF with logo."""
    obj = get_object_or_404(Payroll, pk=pk)
    year, month = obj.periode.year, obj.periode.month

    folder = _media_month_folder(year, month)
    filename = f"pay_{obj.employee.pk}_{year}-{month:02d}.pdf"
    pdf_path = os.path.join(folder, filename)

    generate_paie_pdf(obj, pdf_path)
    return FileResponse(open(pdf_path, "rb"), as_attachment=True, filename=filename)


# -----------------------------
# 📦 ZIP ALL PDFs FOR A MONTH
# -----------------------------
@login_required
def bulk_zip_month(request, year, month):
    """Create a ZIP with all payroll PDFs for the selected month."""
    periode = _periode_date(year, month)
    folder = _media_month_folder(year, month)

    for p in Payroll.objects.filter(periode=periode):
        pdf_path = os.path.join(folder, f"pay_{p.employee.pk}_{year}-{month:02d}.pdf")
        if not os.path.exists(pdf_path):
            generate_paie_pdf(p, pdf_path)

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in sorted(os.listdir(folder)):
            if fname.endswith(".pdf"):
                zf.write(os.path.join(folder, fname), arcname=fname)

    mem.seek(0)
    resp = HttpResponse(mem.read(), content_type="application/zip")
    resp["Content-Disposition"] = f'attachment; filename="payroll_{year}-{month:02d}.zip"'
    return resp


# -----------------------------
# 📤 EXPORT TO EXCEL
# -----------------------------
@login_required
def payroll_export_excel(request):
    """Export payroll data to Excel (filtered by month/year/company/type/currency)."""
    qs = Payroll.objects.select_related("employee").all()

    # Filters
    year = request.GET.get("year")
    month = request.GET.get("month")
    company = request.GET.get("contract_company")
    contract_type = request.GET.get("contract_type")
    devise = request.GET.get("devise")

    if year and month:
        qs = qs.filter(periode__year=year, periode__month=month)
    elif year:
        qs = qs.filter(periode__year=year)
    if company:
        qs = qs.filter(employee__project__icontains=company)
    if contract_type:
        qs = qs.filter(employee__project__icontains=contract_type)
    if devise:
        qs = qs.filter(devise__iexact=devise)

    data = []
    for p in qs:
        e = p.employee
        salary = float(p.salaire_base or 0)
        overtime = float(getattr(p, "heures_supp", 0) or 0)
        overtime_amount = float(getattr(p, "montant_heures_supp", 0) or 0)
        others = float(getattr(p, "autres", 0) or 0)
        deduction = float(getattr(p, "deduction", 0) or 0)
        total = salary + overtime_amount + others - deduction

        data.append({
            "Employee Name": f"{e.prenom} {e.nom}",
            "Zoho ID": getattr(e, "zoho_id", ""),
            "Country": e.country or "",
            "Salary USD": salary,
            "Overtime Hours": overtime,
            "Overtime Amount": overtime_amount,
            "Others": others,
            "Total": total,
            "Month": p.periode.strftime("%B") if p.periode else "",
            "Year": p.periode.year if p.periode else "",
            "Currency": p.devise or "",
        })

    if not data:
        messages.warning(request, "No payroll data found for the selected filters.")
        return redirect("payroll:payroll_list")

    df = pd.DataFrame(data)
    df["Export Date"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    filename = f"payroll_export_{year or 'all'}_{month or 'all'}.xlsx"
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Payroll")

    return response

import pandas as pd
from datetime import datetime
from django.db.models import F
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .models import Payroll
from employees.models import Employee

@never_cache
@login_required
def payroll_stats(request):
    """Comparaison des paies entre deux mois/années, par devise et par employés."""

    # --- Lecture des périodes ---
    month1 = int(request.GET.get("month1", 10))
    year1 = int(request.GET.get("year1", 2025))
    month2 = int(request.GET.get("month2", 11))
    year2 = int(request.GET.get("year2", 2025))

    # --- Extraction directe depuis la BDD ---
    qs1 = Payroll.objects.filter(periode__year=year1, periode__month=month1).values(
        "employee_id", "devise", "total_paye"
    )
    qs2 = Payroll.objects.filter(periode__year=year2, periode__month=month2).values(
        "employee_id", "devise", "total_paye"
    )

    # Conversion en DataFrame
    df1 = pd.DataFrame(list(qs1))
    df2 = pd.DataFrame(list(qs2))

    # Si vide → DataFrame vide avec colonnes
    if df1.empty:
        df1 = pd.DataFrame(columns=["employee_id", "devise", "total_paye"])
    if df2.empty:
        df2 = pd.DataFrame(columns=["employee_id", "devise", "total_paye"])

    # --- Calcul des totaux par devise ---
    totals_1 = df1.groupby("devise", dropna=False)["total_paye"].sum().to_dict()
    totals_2 = df2.groupby("devise", dropna=False)["total_paye"].sum().to_dict()

    all_currencies = set(totals_1.keys()) | set(totals_2.keys())
    totals = {}
    for cur in all_currencies:
        v1 = totals_1.get(cur, 0)
        v2 = totals_2.get(cur, 0)
        totals[cur] = {
            "period1": round(v1, 2),
            "period2": round(v2, 2),
            "difference": round(v2 - v1, 2),
        }

    # --- Identification des employés ---
    emp_1 = set(df1["employee_id"])
    emp_2 = set(df2["employee_id"])

    # INNER JOIN = employés communs
    common_ids = emp_1 & emp_2
    # LEFT ANTI JOIN = employés sortants
    left_only_ids = emp_1 - emp_2
    # RIGHT ANTI JOIN = nouveaux employés
    right_only_ids = emp_2 - emp_1

    common_employees = Employee.objects.filter(id__in=common_ids)
    new_employees = Employee.objects.filter(id__in=right_only_ids)
    left_employees = Employee.objects.filter(id__in=left_only_ids)

    context = {
        "month1": month1,
        "year1": year1,
        "month2": month2,
        "year2": year2,
        "totals": totals,
        "new_employees": new_employees,
        "left_employees": left_employees,
        "common_employees": common_employees,
    }

    return render(request, "payroll/payroll_stats.html", context)

