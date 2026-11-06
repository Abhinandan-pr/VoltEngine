class PrepaidMonthlyInvoice:

    def generate(self, consumer, ledger_entries, month):

        summary = {
            "energy": 0,
            "fixed": 0,
            "duty": 0,
            "dps": 0,
            "installment": 0,
            "excessDemand": 0,
        }

        for e in ledger_entries:
            entry_type = e["type"].strip().lower()
            aliases = {
                "installment_recovery": "installment",
                "excess_demand_penalty": "excessDemand",
                "excessdemand": "excessDemand",
            }
            entry_type = aliases.get(entry_type, entry_type)
            if entry_type in summary:
                summary[entry_type] += e["amount"]

        return {
            "consumerId": consumer.consumer_id,
            "month": month,
            "totalCharges": sum(summary.values()),
            "summary": summary,
            "closingWallet": consumer.wallet_balance,
            "closingArrear": consumer.arrear_balance
        }
