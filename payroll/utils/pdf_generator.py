import os
from datetime import datetime
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_paie_pdf(payroll, output_path):
    """
    Generates a professional payroll PDF (payslip) with logo, contact header, and salary details.
    - Adds 'hello@coorb.io | www.coorb.io' in header
    - Removes employee name from PAYSLIP title
    - Keeps only Name and Title in Employee Info
    """

    # --- Styles ---
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", fontSize=18, alignment=1, textColor=colors.HexColor("#0a4da3"))
    header_text_style = ParagraphStyle("HeaderText", fontSize=9, textColor=colors.HexColor("#555"))
    section_title = ParagraphStyle("SectionTitle", fontSize=12, textColor=colors.HexColor("#0a4da3"), spaceAfter=8)
    normal = ParagraphStyle("Normal", fontSize=10, leading=14)

    # --- Document ---
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=60,
        bottomMargin=40,
    )
    content = []

    # --- ✅ Logo (176x81 px) ---
    possible_logo_paths = [
        os.path.join(settings.BASE_DIR, "payroll", "static", "payroll", "images", "logo.png"),
        os.path.join(settings.BASE_DIR, "payroll", "static", "payroll", "Images", "logo.png"),
        os.path.join(settings.STATIC_ROOT or "", "payroll", "images", "logo.png"),
    ]
    logo_path = next((p for p in possible_logo_paths if os.path.exists(p)), None)
    if logo_path:
        logo = Image(logo_path, width=176, height=81)
        logo.hAlign = "LEFT"
        content.append(logo)
    else:
        print("⚠️ Logo not found, skipping image header")

    # --- Contact line ---
    contact_line = Paragraph("hello@coorb.io  |  www.coorb.io", header_text_style)
    content.append(contact_line)
    content.append(Spacer(1, 15))

    # --- Header title (without employee name) ---
    title_text = "PAYSLIP"
    content.append(Paragraph(title_text, title_style))
    content.append(Spacer(1, 12))

    # --- Period ---
    try:
        periode_text = f"Period: {payroll.periode.strftime('%B %Y')}"
    except Exception:
        periode_text = f"Period: {getattr(payroll, 'periode', '—')}"
    content.append(Paragraph(periode_text, normal))
    content.append(Spacer(1, 15))

    # --- Employee Info (only Name & Title)
    info_data = [
        ["Name:", f"{payroll.employee.prenom} {payroll.employee.nom}"],
        ["Title:", getattr(payroll.employee, "title", "—")],
    ]
    table_info = Table(info_data, colWidths=[100, 350])
    table_info.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    content.append(table_info)
    content.append(Spacer(1, 15))

    # --- Payroll Details ---
    content.append(Paragraph("Remuneration Details", section_title))
    data = [
        ["Element", "Amount", "Comment"],
        ["Base Salary", f"{payroll.salaire_base:.2f} {payroll.devise}", ""],
        ["Overtime", f"{payroll.heures_supp} h → {payroll.montant_heures_supp:.2f} {payroll.devise}", ""],
        ["Reimbursement", f"{payroll.remboursement:.2f} {payroll.devise}", payroll.remboursement_comment or ""],
        ["Others", f"{payroll.autres:.2f} {payroll.devise}", payroll.autres_comment or ""],
        ["Deduction", f"- {payroll.deduction:.2f} {payroll.devise}", ""],
        ["", "", ""],
        ["💰 Total Net Payable", f"{payroll.total_paye:.2f} {payroll.devise}", ""],
    ]
    table = Table(data, colWidths=[200, 120, 200])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0a4da3")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.whitesmoke, colors.lightgrey]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e8f5e9")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    content.append(table)
    content.append(Spacer(1, 25))

    # --- Footer ---
    today = datetime.now().strftime("%d/%m/%Y at %H:%M")
    footer_text = f"Payslip automatically generated on {today}"
    content.append(Paragraph(footer_text, ParagraphStyle("Footer", fontSize=8, textColor=colors.HexColor("#777"))))

    # --- PDF build ---
    doc.build(content)
