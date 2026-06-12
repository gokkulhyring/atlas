from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Atlas", {"fields": ("is_recon_admin", "currently_selected_company")}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
