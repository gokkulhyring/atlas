from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import Account
from transactions.models import Transaction

# (transaction_number, datetime, credit, debit)
SAMPLE = [
    ("PSP-1001", "2024-01-15 09:00:00", "100.00", "0"),    # matches a PSP txn
    ("PSP-1002", "2024-01-15 11:30:00", "250.50", "0"),    # matches a PSP txn
    ("ATLAS-9001", "2024-01-16 10:00:00", "42.00", "0"),   # ATLAS-only (no PSP match)
]


class Command(BaseCommand):
    help = "Seed a few ATLAS-side transactions for reconciliation testing."

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.order_by("id").first()
        account = (
            Account.objects.filter(account_type="bank").order_by("id").first()
            or Account.objects.order_by("id").first()
        )
        if not user or not account:
            self.stderr.write("Need at least one user and one account first.")
            return

        for txn_no, dt, credit, debit in SAMPLE:
            Transaction.objects.update_or_create(
                transaction_number=txn_no,
                defaults={
                    "account_id": account,
                    "user_id": user,
                    "refrence_number": txn_no,
                    "credit_amount": Decimal(credit),
                    "debit_amount": Decimal(debit),
                    "currency": "AUD",
                    "transaction_source": "seed",
                    "transaction_date": datetime.strptime(dt, "%Y-%m-%d %H:%M:%S").date(),
                    "transaction_datetime": datetime.strptime(dt, "%Y-%m-%d %H:%M:%S"),
                    "description": f"Seeded {txn_no}",
                },
            )
        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(SAMPLE)} ATLAS transactions on account '{account}'."
        ))
