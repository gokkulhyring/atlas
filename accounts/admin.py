from django.contrib import admin

from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "account_number", "name", "company_id", "account_mode",
        "account_type", "account_currency", "account_balance", "status",
    )
    search_fields = ("account_number", "name")
    list_filter = ("company_id", "account_mode", "account_type")
