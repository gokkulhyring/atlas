from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand

from atlas.dynamo import get_dynamo_resource

SAMPLE_PSP_BANK_ID = 1

# (transaction_date, transaction_number, credit, debit, customer_email)
SAMPLE_TRANSACTIONS = [
    ("2024-01-15 09:00:00", "PSP-1001", "100.00", "0", "alice@example.com"),
    ("2024-01-15 11:30:00", "PSP-1002", "250.50", "0", "bob@example.com"),
    ("2024-01-16 14:05:00", "PSP-1003", "0", "75.00", "carol@example.com"),
    ("2024-01-16 16:45:00", "PSP-1004", "500.00", "0", "dave@example.com"),
]


class Command(BaseCommand):
    help = "Create the local DynamoDB PSP table (if missing) and seed sample transactions."

    def handle(self, *args, **options):
        dynamodb = get_dynamo_resource()
        table_name = settings.DYNAMODB_TABLE

        if table_name not in [t.name for t in dynamodb.tables.all()]:
            self.stdout.write(f"Creating table {table_name} ...")
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "psp_bank_id", "KeyType": "HASH"},
                    {"AttributeName": "transaction_date", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "psp_bank_id", "AttributeType": "N"},
                    {"AttributeName": "transaction_date", "AttributeType": "S"},
                ],
                BillingMode="PAY_PER_REQUEST",
            )
            table.wait_until_exists()
            self.stdout.write(self.style.SUCCESS(f"Created {table_name}."))
        else:
            table = dynamodb.Table(table_name)
            self.stdout.write(f"Table {table_name} already exists.")

        for txn_date, txn_no, credit, debit, email in SAMPLE_TRANSACTIONS:
            table.put_item(Item={
                "psp_bank_id": SAMPLE_PSP_BANK_ID,
                "transaction_date": txn_date,
                "transaction_datetime": txn_date,
                "transaction_number": txn_no,
                "credit_amount": Decimal(credit),
                "debit_amount": Decimal(debit),
                "customer_email": email,
                "currency": "AUD",
            })
        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(SAMPLE_TRANSACTIONS)} PSP transactions for psp_bank_id={SAMPLE_PSP_BANK_ID}."
        ))
