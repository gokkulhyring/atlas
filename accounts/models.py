from django.db import models

from companies.models import Company

STATUS_CHOICES = (("active", "Active"), ("deactive", "Deactive"))

MODE_CHOICES = (("header", "Header"), ("detail", "Detail"))

CLASSIFICATION_CHOICES = (
    ("asset", "Asset"),
    ("liability", "Liability"),
    ("equity", "Equity"),
    ("income", "Income"),
)

TYPES_CHOICES = (
    ("asset", "Asset"),
    ("bank", "Bank"),
    ("accounts_receivable", "Accounts Receivable"),
    ("other_current_asset", "Other Current Asset"),
    ("fixed_asset", "Fixed Asset"),
    ("other_asset", "Other Asset"),
    ("liability", "Liability"),
    ("credit_card", "Credit Card"),
    ("accounts_payable", "Accounts Payable"),
    ("long_term_liability", "Long Term Liability"),
    ("other_liability", "Other Liability"),
    ("equity", "Equity"),
    ("income", "Income"),
    ("cost_of_sales", "Cost of Sales"),
    ("expense", "Expense"),
    ("other_income", "Other Income"),
    ("other_expense", "Other Expense"),
)

TAX_CODE_CHOICES = (("N-T", "N-T"), ("T", "T"))

YES_NO_CHOICES = (("yes", "Yes"), ("no", "No"))


class Account(models.Model):
    class Meta:
        db_table = "accounts"

    id = models.AutoField(primary_key=True)
    parent_id = models.ForeignKey(
        "self", on_delete=models.CASCADE, db_column="parent_id", blank=True, null=True
    )
    exchange_parent_id = models.IntegerField(blank=True, null=True)
    company_id = models.ForeignKey(Company, on_delete=models.CASCADE, db_column="company_id")
    account_mode = models.CharField(max_length=20, choices=MODE_CHOICES, default="header")
    account_classification = models.CharField(
        max_length=50, choices=CLASSIFICATION_CHOICES, default="asset"
    )
    account_type = models.CharField(max_length=50, choices=TYPES_CHOICES, default="asset")
    account_number = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    account_currency = models.CharField(max_length=4)
    account_balance = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    tax_code = models.CharField(max_length=50, choices=TAX_CODE_CHOICES, default="N-T")
    account_level = models.IntegerField(default=1)
    account_hierarchy = models.CharField(max_length=50, default="", blank=True, null=True)
    account_note = models.TextField(blank=True, null=True)
    show_on_dashboard = models.CharField(max_length=3, choices=YES_NO_CHOICES, default="no")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.account_number + " - " + self.name
