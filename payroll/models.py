from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from employees.models import Employee


class Payroll(models.Model):
    """
    Modèle représentant une fiche de paie pour un employé donné
    et une période mensuelle spécifique.
    """
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="payrolls",
        verbose_name="Employé"
    )

    # Premier jour du mois concerné (ex: 2025-11-01)
    periode = models.DateField(verbose_name="Période")

    salaire_base = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    devise = models.CharField(max_length=10, default="EUR")

    heures_supp = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    montant_heures_supp = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    remboursement = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remboursement_comment = models.TextField(blank=True, null=True)

    nb_conges = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    autres = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    autres_comment = models.TextField(blank=True, null=True)

    total_paye = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_maj = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payroll"  # ✅ Table MySQL fixe
        unique_together = ("employee", "periode")
        ordering = ["-periode", "id"]  # ⚠️ 'employee__nom' n’est pas valide ici
        verbose_name = "Fiche de paie"
        verbose_name_plural = "Fiches de paie"

    def __str__(self):
        return f"{self.employee} - {self.periode:%Y-%m}"

    # --- Recalcul automatique des montants ---
    def _recalc(self):
        """
        Calcule le montant des heures supplémentaires et le total à payer.
        Convention : 1h supp = salaire_base / 173.
        """
        try:
            base = Decimal(self.salaire_base or 0)
            heures_supp = Decimal(self.heures_supp or 0)
            remboursement = Decimal(self.remboursement or 0)
            autres = Decimal(self.autres or 0)
            deduction = Decimal(self.deduction or 0)
        except Exception:
            base = Decimal(0)
            heures_supp = Decimal(0)
            remboursement = Decimal(0)
            autres = Decimal(0)
            deduction = Decimal(0)

        taux_h = (base / Decimal(198)) if base > 0 else Decimal(0)
        self.montant_heures_supp = (taux_h * heures_supp).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total = base + self.montant_heures_supp + remboursement + autres - deduction
        self.total_paye = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        """Avant chaque sauvegarde, recalcule le total automatiquement."""
        self._recalc()
        super().save(*args, **kwargs)
