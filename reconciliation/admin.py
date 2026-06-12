from django.contrib import admin

from .models import Reconcile, ReconcileTransactionLogs


@admin.register(Reconcile)
class ReconcileAdmin(admin.ModelAdmin):
    list_display = (
        "id", "company_id", "psp_bank_id", "account_id", "reconcile_date",
        "psp_opening_balance", "psp_closing_balance", "total_amentments", "created_at",
    )
    list_filter = ("psp_bank_id", "reconcile_date")


@admin.register(ReconcileTransactionLogs)
class ReconcileTransactionLogsAdmin(admin.ModelAdmin):
    list_display = (
        "id", "psp_bank_id", "reconcile_date", "user_id", "event_type",
        "reference_number", "comment", "created_at",
    )
    list_filter = ("event_type", "psp_bank_id")
    search_fields = ("reference_number",)
