from django.conf import settings
from django.db import models

STATUS_CHOICES = (("active", "Active"), ("deactive", "Deactive"))

# Trimmed for the demo — the real app lists 25 currencies in companies/models.py.
CURRENCY_CHOICES = (
    ("AUD", "AUD"), ("USD", "USD"), ("EUR", "EUR"), ("GBP", "GBP"), ("INR", "INR"),
)


class Company(models.Model):
    class Meta:
        db_table = "companies"

    id = models.AutoField(primary_key=True)
    parent_id = models.ForeignKey(
        "self", on_delete=models.CASCADE, db_column="parent_id", blank=True, null=True
    )
    user_id = models.ManyToManyField(
        settings.AUTH_USER_MODEL, db_table="companies_users", related_name="user_id", blank=True
    )
    name = models.CharField(max_length=100)
    base_currency = models.CharField(choices=CURRENCY_CHOICES, max_length=4, default="AUD")
    financial_year_end = models.DateField(default="2020-06-30")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
