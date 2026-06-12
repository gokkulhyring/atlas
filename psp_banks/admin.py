from django.contrib import admin

from .models import PspBank, PspCustomers, PspTransactionsBatch


@admin.register(PspBank)
class PspBankAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "company_id", "account_id", "status", "created_at")
    search_fields = ("name",)


admin.site.register(PspCustomers)
admin.site.register(PspTransactionsBatch)
