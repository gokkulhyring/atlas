from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Demo user model. Real Atlas adds a custom password-hashing signal;
    we skip that — Django's auth forms already hash passwords."""

    is_recon_admin = models.BooleanField(default=False)
    # Real app uses default=1 (a hard dependency on company id 1 existing).
    # We make it nullable to avoid that bootstrap headache while learning.
    currently_selected_company = models.ForeignKey(
        "companies.Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_users",
    )

    def __str__(self):
        return self.username
