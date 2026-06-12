from django.conf import settings
from django.db import connection, models

from accounts.models import Account
from companies.models import Company

STATUS_CHOICES = (("active", "Active"), ("deactive", "Deactive"))

UPLOAD_STATUS_CHOICES = (
    ("pending", "Pending"),
    ("processing", "Processing"),
    ("processed", "Processed"),
    ("failed", "Failed"),
)


class PspBank(models.Model):
    class Meta:
        db_table = "psp_banks"
        unique_together = (("name", "company_id"),)

    id = models.AutoField(primary_key=True)
    account_id = models.ForeignKey(Account, on_delete=models.DO_NOTHING, db_column="account_id")
    company_id = models.ForeignKey(Company, on_delete=models.DO_NOTHING, db_column="company_id")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    transaction_filters = models.JSONField(blank=True, null=True)
    credit_column_rules = models.JSONField(blank=True, null=True)
    debit_column_rules = models.JSONField(blank=True, null=True)
    attribute_mapping = models.JSONField()
    matching_rules = models.JSONField()
    psp_data_schema = models.JSONField()
    cut_off_time = models.TimeField(blank=True, null=True, default="23:59:59")
    opening_balance = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    psp_reserve_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PspCustomers(models.Model):
    class Meta:
        db_table = "psp_customers"

    id = models.AutoField(primary_key=True)
    company_id = models.ForeignKey(Company, on_delete=models.DO_NOTHING, db_column="company_id")
    name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True, unique=True)
    currency = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def truncate(cls):
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {cls._meta.db_table}")


class PspTransactionsBatch(models.Model):
    class Meta:
        db_table = "psp_transactions_batch"

    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id"
    )
    psp_bank_id = models.ForeignKey(PspBank, on_delete=models.DO_NOTHING, db_column="psp_bank_id")
    total_records = models.IntegerField(default=0)
    file_name = models.CharField(max_length=200, default="")
    response_text = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=UPLOAD_STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    s3_file_name = models.CharField(max_length=255, default="")
    is_deleted = models.IntegerField(default=0)
