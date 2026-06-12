from boto3.dynamodb.conditions import Key
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views import View

from atlas.dynamo import get_psp_table
from psp_banks.models import PspBank
from transactions.models import Transaction


@method_decorator(login_required, name="get")
class ReconciliationView(View):
    """Simplified reconciliation. Loads the PSP side (DynamoDB) and the ATLAS side
    (MySQL) for a PSP bank + date, then matches them per the bank's matching_rules.
    Real Atlas matches interactively in the browser; we match server-side so the
    workflow is easy to follow."""

    template_name = "reconciliation/reconcile_result.html"

    def fetch_psp_transactions(self, psp_bank, from_date, to_date):
        # Same boto3 query shape as the real app — just against local DynamoDB.
        table = get_psp_table()
        response = table.query(
            KeyConditionExpression=(
                Key("psp_bank_id").eq(psp_bank.id)
                & Key("transaction_date").between(from_date, to_date)
            ),
        )
        items = response["Items"]
        while response.get("LastEvaluatedKey"):
            response = table.query(
                KeyConditionExpression=(
                    Key("psp_bank_id").eq(psp_bank.id)
                    & Key("transaction_date").between(
                        response["LastEvaluatedKey"]["transaction_date"], to_date
                    )
                ),
            )
            items += response["Items"]
        return items

    def normalize_psp(self, psp_bank, items):
        # Rename raw PSP columns to canonical names via attribute_mapping
        # ({canonical: source}); mirrors pre_process_transactions_df, minus pandas.
        mapping = psp_bank.attribute_mapping or {}
        return [
            {canonical: item.get(source, "") for canonical, source in mapping.items()}
            for item in items
        ]

    def get(self, request):
        psp_banks = PspBank.objects.filter(status="active").order_by("name")
        psp_bank_id = request.GET.get("psp_bank_id")
        reconcile_date = request.GET.get("reconcile_date")

        context = {
            "psp_banks": psp_banks,
            "psp_bank_id": psp_bank_id,
            "reconcile_date": reconcile_date,
        }

        # Show just the picker until both inputs are provided.
        if not psp_bank_id or not reconcile_date:
            return render(request, self.template_name, context)

        psp_bank = get_object_or_404(PspBank, id=psp_bank_id)

        # PSP-side window = the whole reconcile day (real app narrows by cut_off_time).
        from_date = f"{reconcile_date} 00:00:00"
        to_date = f"{reconcile_date} 23:59:59"
        psp_rows = self.normalize_psp(
            psp_bank, self.fetch_psp_transactions(psp_bank, from_date, to_date)
        )

        # ATLAS side: same account + date, excluding invoice/amended (real app's filter).
        atlas_txns = list(
            Transaction.objects.filter(
                account_id=psp_bank.account_id,
                transaction_date=reconcile_date,
                is_invoice_transaction="no",
                is_reconcile_amended="no",
            ).order_by("-id")
        )

        # Match on the bank's matching_rules (default: transaction_number).
        rules = psp_bank.matching_rules or ["transaction_number"]

        def atlas_key(t):
            return tuple(str(getattr(t, r, "") or "").strip() for r in rules)

        def psp_key(row):
            return tuple(str(row.get(r, "") or "").strip() for r in rules)

        atlas_index = {}
        for t in atlas_txns:
            atlas_index.setdefault(atlas_key(t), []).append(t)

        matched, psp_unrec, used = [], [], set()
        for row in psp_rows:
            bucket = atlas_index.get(psp_key(row), [])
            partner = next((t for t in bucket if t.id not in used), None)
            if partner:
                used.add(partner.id)
                matched.append({"psp": row, "atlas": partner})
            else:
                psp_unrec.append(row)

        atlas_unrec = [t for t in atlas_txns if t.id not in used]

        context.update({
            "has_result": True,
            "psp_bank": psp_bank,
            "matching_rules": rules,
            "matched": matched,
            "psp_unrec": psp_unrec,
            "atlas_unrec": atlas_unrec,
        })
        return render(request, self.template_name, context)