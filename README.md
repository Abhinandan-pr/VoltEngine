# ⚡ VoltEngine
**The Universal Utility Billing Framework**

VoltEngine is an industry-ready Python library designed to automate complex electricity billing cycles. From simple domestic slab rates (LT) to complex industrial demand charges (HT), VoltEngine provides a modular math-heavy core to ensure zero-error invoicing.

## 🎯 Domain Coverage
- **LT Postpaid:** Residential/Commercial slab-based billing.
- **LT Prepaid:** Real-time credit-to-energy conversion logic.
- **HT (High Tension):** Industrial billing featuring Demand Charges, Power Factor (PF) adjustments, and Time-of-Day (ToD) tariffs.

## ⚙️ Core Logic Flow
The engine processes data through a structured pipeline to ensure compliance with regulatory standards:

1. **Input Layer:** Consumes KWh (Active), KVAh (Apparent), and MD (Maximum Demand).
2. **Tariff Resolver:** Matches consumer type to specific state/utility rate cards.
3. **Calculation Engine:** Processes fixed charges, energy charges, and penalties.
4. **Taxation Module:** Applies Duty, GST, and Surcharges.
5. **Output Layer:** Generates a structured JSON objects ready for PDF invoicing or API consumption.



## 🛠️ Tech Stack
- **Engine:** Python 3.10+ (Logic & Math)
- **Validation:** Pydantic (Data integrity)
- **API Layer:** FastAPI (High-speed integration)
- **UI/Simulator:** Streamlit (For real-time billing simulation)

## HTTP Billing API

The FastAPI service exposes daily prepaid billing, monthly invoice summaries, and wallet recharge endpoints. It is stateless: the caller sends current consumer, tariff, and meter details, then saves returned balances and ledger entries in its own system.

Every billing endpoint requires **both** an allowlisted API key and an allowlisted client IP address. Access is disabled until both lists are configured. Keep keys secret and set them in the deployment environment; do not commit them to this repository.

```powershell
python -m pip install -e ".[api]"
$env:VOLTENGINE_API_KEYS = "replace-with-a-long-random-key"
$env:VOLTENGINE_ALLOWED_IPS = "203.0.113.10,198.51.100.0/24"
python -m uvicorn http_api:app --host 0.0.0.0 --port 8000
```

`/health` is public and returns service status. Billing routes are protected. Interactive API documentation is available at `/docs`.

### Daily billing request

Send `POST /v1/billing/daily` with the `X-API-Key` header and JSON such as:

```json
{
  "consumer": {
    "consumer_id": "C-1001",
    "wallet_balance": 500.0,
    "arrear_balance": 120.0,
    "load_kw": 3.0,
    "installment": {"total": 120.0, "daily": 2.0, "tenureDays": 60}
  },
  "meter": {"daily_units": 8.5, "max_demand_kw": 2.4},
  "tariff": {
    "slabs": [
      {"upto": 50, "rate": 3.1},
      {"upto": 100, "rate": 3.6},
      {"upto": null, "rate": 4.1}
    ],
    "fixed_charge": 120,
    "duty_rate": 0.05,
    "dps_monthly_rate": 0.015,
    "demand_rate": 250,
    "excess_demand_multiplier": 1.5
  },
  "period_days": 30,
  "billing_date": "2026-11-06"
}
```

The response contains the charge breakdown, updated wallet and arrear balances, and ledger entries. The final tariff slab must use `"upto": null`. Use `POST /v1/billing/monthly` with account balances and ledger lines for a month summary, or `POST /v1/billing/recharge` to apply a recharge.

When deploying behind a reverse proxy, configure the ASGI server to trust forwarded client addresses only from that proxy. The IP allowlist checks the connection address seen by the app; do not trust arbitrary client-supplied `X-Forwarded-For` values.
