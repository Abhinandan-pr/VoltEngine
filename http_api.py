"""HTTP API for VoltEngine billing operations.

Access is opt-in: configure both VOLTENGINE_API_KEYS and
VOLTENGINE_ALLOWED_IPS. A request must match an allowlisted key and originate
from an allowlisted address or network.
"""

from __future__ import annotations

import ipaddress
import os
import secrets
from datetime import date
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from accounting.ledger_engine import LedgerEngine
from billing.prepaid_daily import PrepaidDailyBilling
from billing.prepaid_monthly import PrepaidMonthlyInvoice
from models.consumer import Consumer
from models.meter import Meter
from models.period import Period
from models.tariff import Tariff
from operations.recharge import RechargeOperation


class InstallmentInput(BaseModel):
    total: float = Field(ge=0, allow_inf_nan=False)
    daily: float = Field(ge=0, allow_inf_nan=False)
    tenureDays: int = Field(gt=0)


class ConsumerInput(BaseModel):
    consumer_id: str = Field(min_length=1, max_length=128)
    wallet_balance: float = Field(allow_inf_nan=False)
    arrear_balance: float = Field(ge=0, allow_inf_nan=False)
    load_kw: float = Field(gt=0, allow_inf_nan=False)
    installment: Optional[InstallmentInput] = None


class MeterInput(BaseModel):
    daily_units: float = Field(ge=0, allow_inf_nan=False)
    max_demand_kw: float = Field(ge=0, allow_inf_nan=False)


class SlabInput(BaseModel):
    # `upto=None` is the open-ended final slab.
    upto: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    rate: float = Field(ge=0, allow_inf_nan=False)


class TariffInput(BaseModel):
    slabs: List[SlabInput] = Field(min_length=1)
    fixed_charge: float = Field(ge=0, allow_inf_nan=False)
    duty_rate: float = Field(ge=0, allow_inf_nan=False)
    dps_monthly_rate: float = Field(ge=0, allow_inf_nan=False)
    demand_rate: float = Field(ge=0, allow_inf_nan=False)
    excess_demand_multiplier: float = Field(ge=0, allow_inf_nan=False)


class DailyBillingRequest(BaseModel):
    consumer: ConsumerInput
    meter: MeterInput
    tariff: TariffInput
    period_days: int = Field(gt=0, le=366)
    billing_date: date


class RechargeRequest(BaseModel):
    consumer_id: str = Field(min_length=1, max_length=128)
    wallet_balance: float = Field(allow_inf_nan=False)
    arrear_balance: float = Field(ge=0, allow_inf_nan=False)
    load_kw: float = Field(gt=0, allow_inf_nan=False)
    installment: Optional[InstallmentInput] = None
    amount: float = Field(gt=0, allow_inf_nan=False)
    revise_installment: bool = True


class LedgerLine(BaseModel):
    type: str
    amount: float = Field(ge=0, allow_inf_nan=False)


class MonthlyInvoiceRequest(BaseModel):
    consumer_id: str = Field(min_length=1, max_length=128)
    wallet_balance: float = Field(allow_inf_nan=False)
    arrear_balance: float = Field(ge=0, allow_inf_nan=False)
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    ledger_entries: List[LedgerLine] = Field(default_factory=list)


def _split_allowlist(variable: str) -> List[str]:
    return [value.strip() for value in os.getenv(variable, "").split(",") if value.strip()]


def _allowed_networks() -> List[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    networks = []
    for value in _split_allowlist("VOLTENGINE_ALLOWED_IPS"):
        try:
            networks.append(ipaddress.ip_network(value, strict=False))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Billing API IP allowlist is misconfigured.",
            ) from exc
    return networks


async def require_allowlisted_client(
    request: Request,
    api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> None:
    allowed_keys = _split_allowlist("VOLTENGINE_API_KEYS")
    networks = _allowed_networks()
    if not allowed_keys or not networks:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Billing API access is not configured.",
        )

    if not api_key or not any(secrets.compare_digest(api_key, key) for key in allowed_keys):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid allowlisted X-API-Key is required.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    client_host = request.client.host if request.client else None
    try:
        client_ip = ipaddress.ip_address(client_host) if client_host else None
    except ValueError:
        client_ip = None
    if client_ip is None or not any(client_ip in network for network in networks):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client IP address is not allowlisted.",
        )


app = FastAPI(
    title="VoltEngine Billing API",
    version="1.0.0",
    description="Stateless prepaid billing endpoints protected by API-key and IP allowlists.",
)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "voltengine-billing"}


@app.post("/v1/billing/daily", dependencies=[Depends(require_allowlisted_client)], tags=["billing"])
def daily_billing(payload: DailyBillingRequest):
    slabs = [slab.dict() for slab in payload.tariff.slabs]
    if slabs[-1]["upto"] is not None:
        raise HTTPException(status_code=422, detail="The final tariff slab must have upto=null.")
    for previous, current in zip(slabs, slabs[1:]):
        if previous["upto"] is None or current["upto"] is None or current["upto"] <= previous["upto"]:
            raise HTTPException(status_code=422, detail="Tariff slab limits must increase and end with upto=null.")

    consumer_data = payload.consumer
    consumer = Consumer(
        consumer_id=consumer_data.consumer_id,
        wallet_balance=consumer_data.wallet_balance,
        arrear_balance=consumer_data.arrear_balance,
        load_kw=consumer_data.load_kw,
        installment=consumer_data.installment.dict() if consumer_data.installment else None,
    )
    meter = Meter(payload.meter.daily_units, payload.meter.max_demand_kw)
    tariff = Tariff(
        slabs=slabs,
        fixed_charge=payload.tariff.fixed_charge,
        duty_rate=payload.tariff.duty_rate,
        dps_monthly_rate=payload.tariff.dps_monthly_rate,
        demand_rate=payload.tariff.demand_rate,
        excess_demand_multiplier=payload.tariff.excess_demand_multiplier,
    )
    ledger = LedgerEngine()
    result = PrepaidDailyBilling().run(
        consumer=consumer,
        meter=meter,
        tariff=tariff,
        period=Period(payload.period_days),
        ledger=ledger,
        date=payload.billing_date.isoformat(),
    )
    return {"result": result, "ledger": ledger.snapshot()}


@app.post("/v1/billing/monthly", dependencies=[Depends(require_allowlisted_client)], tags=["billing"])
def monthly_invoice(payload: MonthlyInvoiceRequest):
    consumer = Consumer(
        consumer_id=payload.consumer_id,
        wallet_balance=payload.wallet_balance,
        arrear_balance=payload.arrear_balance,
    )
    ledger_entries = [{"type": entry.type.lower(), "amount": entry.amount} for entry in payload.ledger_entries]
    return PrepaidMonthlyInvoice().generate(consumer, ledger_entries, payload.month)


@app.post("/v1/billing/recharge", dependencies=[Depends(require_allowlisted_client)], tags=["billing"])
def recharge(payload: RechargeRequest):
    consumer = Consumer(
        consumer_id=payload.consumer_id,
        wallet_balance=payload.wallet_balance,
        arrear_balance=payload.arrear_balance,
        load_kw=payload.load_kw,
        installment=payload.installment.dict() if payload.installment else None,
    )
    result = RechargeOperation.apply(consumer, payload.amount, payload.revise_installment)
    return {"consumerId": payload.consumer_id, **result}
