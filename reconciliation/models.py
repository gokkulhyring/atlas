from django.conf import settings
from django.db import models

from accounts.models import Account
from companies.models import Company
from psp_banks.models import PspBank

EVENT_CHOICES = (
    ("MODIFIED_TRANSACTION_ATLAS", "MODIFIED_TRANSACTION_ATLAS"),
    ("MODIFIED_TRANSACTION_PSP", "MODIFIED_TRANSACTION_PSP"),
    ("ADDED_TRANSACTION_UNREC_ATLAS", "ADDED_TRANSACTION_UNREC_ATLAS"),
    ("ADDED_TRANSACTION_UNREC_PSP", "ADDED_TRANSACTION_UNREC_PSP"),
    ("MODIFIED_TRANSACTION_UNREC_ATLAS", "MODIFIED_TRANSACTION_UNREC_ATLAS"),
    ("MODIFIED_TRANSACTION_UNREC_PSP", "MODIFIED_TRANSACTION_UNREC_PSP"),
    ("MOVED_TRANSACTION_UNREC_ATLAS", "MOVED_TRANSACTION_UNREC_ATLAS"),
    ("MOVED_TRANSACTION_UNREC_PSP", "MOVED_TRANSACTION_UNREC_PSP"),
    ("ADDED_TRANSACTION_ATLAS", "ADDED_TRANSACTION_ATLAS"),
    ("DELETED_TRANSACTION_ATLAS", "DELETED_TRANSACTION_ATLAS"),
    ("DELETED_TRANSACTION_PSP", "DELETED_TRANSACTION_PSP"),
    ("MODIFIED_OPENING_CLOSING_BALANCE_PSP", "MODIFIED_OPENING_CLOSING_BALANCE_PSP"),
)


class Reconcile(models.Model):
    class Meta:
        db_table = "reconcile_data"

    id = models.AutoField(primary_key=True)
    account_id = models.ForeignKey(Account, on_delete=models.DO_NOTHING, db_column="account_id")
    company_id = models.ForeignKey(Company, on_delete=models.DO_NOTHING, db_column="company_id")
    psp_bank_id = models.ForeignKey(PspBank, on_delete=models.DO_NOTHING, db_column="psp_bank_id")
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, db_column="user_id"
    )
    reconcile_date = models.DateField()
    viewed_by = models.CharField(max_length=100, blank=True, null=True)
    approved_by = models.CharField(max_length=100, blank=True, null=True)
    psp_balance_snapshot = models.CharField(max_length=100, blank=True, null=True)
    total_amentments = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    psp_opening_balance = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    psp_closing_balance = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reconcile {self.id} ({self.reconcile_date})"


class ReconcileTransactionLogs(models.Model):
    class Meta:
        db_table = "reconcile_transaction_logs"

    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, db_column="user_id"
    )
    reconcile_id = models.ForeignKey(
        Reconcile, on_delete=models.DO_NOTHING, db_column="reconcile_id", blank=True, null=True
    )
    psp_bank_id = models.ForeignKey(PspBank, on_delete=models.DO_NOTHING, db_column="psp_bank_id")
    reconcile_date = models.DateField()
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    old_transaction = models.JSONField(blank=True, null=True)
    updated_transaction = models.JSONField(blank=True, null=True)
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
