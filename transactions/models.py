from django.conf import settings
from django.db import models

from accounts.models import Account

YES_NO_CHOICES = (("yes", "Yes"), ("no", "No"))


class Transaction(models.Model):
    class Meta:
        db_table = "transactions"

    id = models.AutoField(primary_key=True)
    # Real app has upload_id (FK JournalUpload) and reverse_transaction (self-FK);
    # both omitted in the demo — reconciliation doesn't use them.
    refrence_number = models.CharField(max_length=20, default="")  # (sic) real app's spelling
    transaction_number = models.CharField(max_length=100, default="")
    reconcile_mapping_hash = models.CharField(max_length=100, blank=True, null=True)
    mapping_hash_date = models.DateField(blank=True, null=True)
    account_id = models.ForeignKey(Account, on_delete=models.CASCADE, db_column="account_id")
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id"
    )
    debit_amount = models.DecimalField(max_digits=16, decimal_places=2, blank=True, null=True)
    credit_amount = models.DecimalField(max_digits=16, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=4, default="AUD")
    opening_balance = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    conversion_rate = models.DecimalField(max_digits=14, decimal_places=8, blank=True, null=True)
    qty = models.CharField(max_length=10, blank=True, null=True)
    item = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    transaction_source = models.CharField(max_length=255, default="manual")
    transaction_date = models.DateField()
    aged_date = models.DateField(blank=True, null=True)
    transaction_datetime = models.DateTimeField(blank=True, null=True)
    invoice_source_id = models.IntegerField(blank=True, null=True)
    invoice_source_type = models.CharField(max_length=20, blank=True, null=True)
    is_invoice_transaction = models.CharField(max_length=3, choices=YES_NO_CHOICES, default="no")
    is_flagged_transaction = models.CharField(max_length=3, choices=YES_NO_CHOICES, default="no")
    is_reconcile_amended = models.CharField(max_length=3, choices=YES_NO_CHOICES, default="no")
    is_cut_off = models.CharField(max_length=3, choices=YES_NO_CHOICES, default="no")
    cut_off_date = models.DateTimeField(blank=True, null=True)
    cut_off_comment = models.TextField(blank=True, null=True)
    is_reverse = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.transaction_number or f"txn-{self.id}"
