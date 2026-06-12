from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id", "transaction_number", "account_id", "debit_amount", "credit_amount",
        "currency", "transaction_date", "is_cut_off", "reconcile_mapping_hash",
    )
    list_filter = ("is_cut_off", "is_reconcile_amended", "currency", "account_id")
    search_fields = ("transaction_number", "refrence_number")
