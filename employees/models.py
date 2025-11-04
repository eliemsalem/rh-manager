from django.db import models
from django.utils import timezone

class Employee(models.Model):
    nom = models.CharField(max_length=100, null=True, blank=True)
    prenom = models.CharField(max_length=100, null=True, blank=True)
    zoho_id = models.CharField(max_length=100, null=True, blank=True)
    project = models.CharField(max_length=100, null=True, blank=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=150, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    lead_1 = models.CharField(max_length=255, null=True, blank=True)
    pt_date = models.DateField(null=True, blank=True)
    ft_date = models.DateField(null=True, blank=True)
    last_day = models.DateField(null=True, blank=True)
    salaire_net = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    devise = models.CharField(max_length=10, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    accomodation = models.CharField(max_length=100, null=True, blank=True)
    contract_type = models.CharField(max_length=100, null=True, blank=True)
    contract_company = models.CharField(max_length=100, null=True, blank=True)
    actif = models.BooleanField(default=True)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    bank_country = models.CharField(max_length=100, null=True, blank=True)
    iban = models.CharField(max_length=255, null=True, blank=True)
    swift = models.CharField(max_length=255, null=True, blank=True)
    date_import = models.DateTimeField(default=timezone.now, editable=False)



    class Meta:
        db_table = 'employee'

    def __str__(self):
        return f"{self.prenom or ''} {self.nom or ''}"
