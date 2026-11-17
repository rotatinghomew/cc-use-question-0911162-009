from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable, Mapping

from member_settlement.accounts.member import stable_hash, utc_now

SETTLEMENT_SCALE = Decimal("0.01")
UNIT_SCALE = Decimal("0.0001")
RATE_SCALE = Decimal("0.00000001")
IDENTITY = Decimal("1")


class ReconciliationError(ValueError):
    """Raised when a reconciliation invariant or closed-period guard is violated."""


def _decimal(value: Any, label: str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool) or value is None:
        raise ReconciliationError(f"{label} must be numeric")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ReconciliationError(f"{label} must be numeric") from exc
    if not result.is_finite():
        raise ReconciliationError(f"{label} must be finite")
    return result


def money(value: Any, label: str = "amount") -> Decimal:
    return _decimal(value, label).quantize(SETTLEMENT_SCALE, rounding=ROUND_HALF_UP)


def units(value: Any, label: str = "units") -> Decimal:
    return _decimal(value, label).quantize(UNIT_SCALE, rounding=ROUND_HALF_UP)


def rate_value(value: Any, label: str = "rate") -> Decimal:
    rate = _decimal(value, label)
    if rate <= 0:
        raise ReconciliationError(f"{label} must be positive")
    return rate.quantize(RATE_SCALE, rounding=ROUND_HALF_UP)


def as_date(value: Any, label: str = "date") -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise ReconciliationError(f"{label} must be an ISO date (YYYY-MM-DD)") from exc


def _iso(value: date) -> str:
    return value.isoformat()


def _s(value: Decimal) -> str:
    return format(value, "f")


def _currency(value: Any, label: str = "currency") -> str:
    text = str(value or "").strip().upper()
    if not text or len(text) > 12 or not all(character.isalnum() or character in "._-" for character in text):
        raise ReconciliationError(f"{label} must be a currency code")
    return text


@dataclass(frozen=True)
class FxRate:
    base: str
    quote: str
    rate: Decimal
    rate_date: date
    source: str = "manual"
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "base", _currency(self.base, "base currency"))
        object.__setattr__(self, "quote", _currency(self.quote, "quote currency"))
        object.__setattr__(self, "rate", rate_value(self.rate))
        object.__setattr__(self, "rate_date", as_date(self.rate_date, "rate date"))
        if self.base == self.quote and self.rate != IDENTITY:
            raise ReconciliationError("identity FX rate must equal 1")

    def as_dict(self) -> dict[str, Any]:
        return {"base": self.base, "quote": self.quote, "rate": _s(self.rate),
                "rate_date": _iso(self.rate_date), "source": self.source}


@dataclass(frozen=True)
class Charge:
    """A bill, denominated in the settlement currency and frozen once its period closes."""

    charge_id: str
    member_id: str
    period_id: str
    currency: str
    amount: Decimal
    issued_on: date
    reference_rate_date: date
    entitlement_units: Decimal
    record_id: str = ""
    version: int = 1
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for name in ("charge_id", "member_id", "period_id"):
            text = str(getattr(self, name) or "").strip()
            if not text:
                raise ReconciliationError(f"{name} is required")
            object.__setattr__(self, name, text)
        object.__setattr__(self, "currency", _currency(self.currency))
        object.__setattr__(self, "amount", money(self.amount, "charge amount"))
        if self.amount < 0:
            raise ReconciliationError("charge amount cannot be negative")
        object.__setattr__(self, "issued_on", as_date(self.issued_on, "issued_on"))
        object.__setattr__(self, "reference_rate_date", as_date(self.reference_rate_date, "reference rate date"))
        object.__setattr__(self, "entitlement_units", units(self.entitlement_units, "entitlement units"))
        if self.entitlement_units < 0:
            raise ReconciliationError("entitlement units cannot be negative")
        if self.version < 1:
            raise ReconciliationError("charge version must be positive")

    def as_dict(self) -> dict[str, Any]:
        return {"charge_id": self.charge_id, "member_id": self.member_id, "record_id": self.record_id,
                "period_id": self.period_id, "currency": self.currency, "amount": _s(self.amount),
                "issued_on": _iso(self.issued_on), "reference_rate_date": _iso(self.reference_rate_date),
                "entitlement_units": _s(self.entitlement_units), "version": self.version}


@dataclass(frozen=True)
class Receipt:
    """A member payment, kept in its original currency with the FX rate and rate date applied."""

    payment_id: str
    member_id: str
    original_currency: str
    original_amount: Decimal
    settlement_currency: str
    paid_on: date
    rate_date: date
    applied_rate: Decimal
    settlement_value: Decimal
    reference: str = ""
    original_period_id: str = ""
    correction_period_id: str = ""
    reversed: bool = False
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for name in ("payment_id", "member_id"):
            text = str(getattr(self, name) or "").strip()
            if not text:
                raise ReconciliationError(f"{name} is required")
            object.__setattr__(self, name, text)
        object.__setattr__(self, "original_currency", _currency(self.original_currency, "original currency"))
        object.__setattr__(self, "settlement_currency", _currency(self.settlement_currency, "settlement currency"))
        object.__setattr__(self, "original_amount", money(self.original_amount, "original amount"))
        if self.original_amount <= 0:
            raise ReconciliationError("original amount must be positive")
        object.__setattr__(self, "paid_on", as_date(self.paid_on, "paid_on"))
        object.__setattr__(self, "rate_date", as_date(self.rate_date, "rate date"))
        object.__setattr__(self, "applied_rate", rate_value(self.applied_rate))
        object.__setattr__(self, "settlement_value", money(self.settlement_value, "settlement value"))
        if self.settlement_value < 0:
            raise ReconciliationError("settlement value cannot be negative")

    def as_dict(self) -> dict[str, Any]:
        return {"payment_id": self.payment_id, "member_id": self.member_id,
                "original_currency": self.original_currency, "original_amount": _s(self.original_amount),
                "settlement_currency": self.settlement_currency, "paid_on": _iso(self.paid_on),
                "rate_date": _iso(self.rate_date), "applied_rate": _s(self.applied_rate),
                "settlement_value": _s(self.settlement_value), "reference": self.reference,
                "original_period_id": self.original_period_id,
                "correction_period_id": self.correction_period_id, "reversed": self.reversed}


@dataclass(frozen=True)
class Allocation:
    allocation_id: str
    payment_id: str
    charge_id: str
    amount: Decimal
    rate: Decimal
    rate_date: date
    correction_period_id: str = ""
    reversed: bool = False
    allocated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for name in ("allocation_id", "payment_id", "charge_id"):
            text = str(getattr(self, name) or "").strip()
            if not text:
                raise ReconciliationError(f"{name} is required")
            object.__setattr__(self, name, text)
        object.__setattr__(self, "amount", money(self.amount, "allocation amount"))
        if self.amount <= 0:
            raise ReconciliationError("allocation amount must be positive")
        object.__setattr__(self, "rate", rate_value(self.rate))
        object.__setattr__(self, "rate_date", as_date(self.rate_date, "rate date"))

    def as_dict(self) -> dict[str, Any]:
        return {"allocation_id": self.allocation_id, "payment_id": self.payment_id,
                "charge_id": self.charge_id, "amount": _s(self.amount), "rate": _s(self.rate),
                "rate_date": _iso(self.rate_date), "correction_period_id": self.correction_period_id,
                "reversed": self.reversed}


@dataclass(frozen=True)
class Waiver:
    waiver_id: str
    charge_id: str
    currency: str
    amount: Decimal
    approved_on: date
    reason: str = ""
    correction_period_id: str = ""
    reversed: bool = False
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not str(self.waiver_id or "").strip():
            raise ReconciliationError("waiver_id is required")
        object.__setattr__(self, "waiver_id", str(self.waiver_id).strip())
        if not str(self.charge_id or "").strip():
            raise ReconciliationError("waiver charge_id is required")
        object.__setattr__(self, "charge_id", str(self.charge_id).strip())
        object.__setattr__(self, "currency", _currency(self.currency))
        object.__setattr__(self, "amount", money(self.amount, "waiver amount"))
        if self.amount <= 0:
            raise ReconciliationError("waiver amount must be positive")
        object.__setattr__(self, "approved_on", as_date(self.approved_on, "approved_on"))

    def as_dict(self) -> dict[str, Any]:
        return {"waiver_id": self.waiver_id, "charge_id": self.charge_id, "currency": self.currency,
                "amount": _s(self.amount), "approved_on": _iso(self.approved_on), "reason": self.reason,
                "correction_period_id": self.correction_period_id, "reversed": self.reversed}


@dataclass(frozen=True)
class ChargeReconciliation:
    charge_id: str
    member_id: str
    period_id: str
    currency: str
    charged: Decimal
    receipts_settled: Decimal
    fx_variance: Decimal
    waiver_amount: Decimal
    outstanding_amount: Decimal
    overpayment_credit: Decimal
    entitlement_units: Decimal
    releasable_units: Decimal
    coverage_ratio: Decimal
    receipts_cash_applied: Decimal
    allocation_ids: tuple[str, ...] = ()
    correction_periods: tuple[str, ...] = ()

    @property
    def explained_amount(self) -> Decimal:
        return (self.receipts_settled + self.fx_variance + self.waiver_amount
                + self.outstanding_amount - self.overpayment_credit)

    @property
    def identity_holds(self) -> bool:
        return self.explained_amount == self.charged

    def as_dict(self) -> dict[str, Any]:
        return {"charge_id": self.charge_id, "member_id": self.member_id, "period_id": self.period_id,
                "currency": self.currency, "charged": _s(self.charged),
                "receipts_settled": _s(self.receipts_settled),
                "receipts_cash_applied": _s(self.receipts_cash_applied),
                "fx_variance": _s(self.fx_variance),
                "waiver_amount": _s(self.waiver_amount), "outstanding_amount": _s(self.outstanding_amount),
                "overpayment_credit": _s(self.overpayment_credit),
                "entitlement_units": _s(self.entitlement_units),
                "releasable_units": _s(self.releasable_units),
                "coverage_ratio": _s(self.coverage_ratio),
                "identity_holds": self.identity_holds,
                "allocation_ids": list(self.allocation_ids),
                "correction_periods": sorted(set(self.correction_periods))}


class ReconciliationBook:
    """Deterministic in-memory reconciliation engine.

    Accounting identity per bill, in the settlement currency::

        charged == receipts_settled + fx_variance + waivers + outstanding - overpayment_credit

    ``outstanding`` therefore only contains genuinely unpaid money; conversion
    differences and approved waivers are reported as their own buckets.
    """

    def __init__(self, settlement_currency: str = "USD"):
        self.settlement_currency = _currency(settlement_currency, "settlement currency")
        self._rates: list[FxRate] = []
        self._charges: dict[str, Charge] = {}
        self._receipts: dict[str, Receipt] = {}
        self._allocations: dict[str, Allocation] = {}
        self._waivers: dict[str, Waiver] = {}
        self._closed: dict[str, dict[str, Any]] = {}
        self._windows: dict[str, tuple[date, date]] = {}
        self._corrections: list[dict[str, Any]] = []

    # ------------------------------------------------------------------ state
    @property
    def rates(self) -> tuple[FxRate, ...]:
        return tuple(self._rates)

    @property
    def charges(self) -> tuple[Charge, ...]:
        return tuple(self._charges.values())

    @property
    def receipts(self) -> tuple[Receipt, ...]:
        return tuple(self._receipts.values())

    @property
    def allocations(self) -> tuple[Allocation, ...]:
        return tuple(self._allocations.values())

    @property
    def waivers(self) -> tuple[Waiver, ...]:
        return tuple(self._waivers.values())

    @property
    def closed_periods(self) -> tuple[str, ...]:
        return tuple(self._closed)

    @property
    def corrections(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._corrections)

    def fingerprint(self) -> str:
        return stable_hash({
            "settlement_currency": self.settlement_currency,
            "rates": [item.as_dict() for item in self._rates],
            "charges": [item.as_dict() for item in self._charges.values()],
            "receipts": [item.as_dict() for item in self._receipts.values()],
            "allocations": [item.as_dict() for item in self._allocations.values()],
            "waivers": [item.as_dict() for item in self._waivers.values()],
            "corrections": list(self._corrections),
            "closed": list(self._closed.values()),
        })

    def restore(self, *, rates: Iterable[FxRate] = (), charges: Iterable[Charge] = (),
                receipts: Iterable[Receipt] = (), allocations: Iterable[Allocation] = (),
                waivers: Iterable[Waiver] = (), corrections: Iterable[Mapping[str, Any]] = (),
                closes: Iterable[Mapping[str, Any]] = (), settlement_currency: str | None = None) -> None:
        if settlement_currency:
            self.settlement_currency = _currency(settlement_currency, "settlement currency")
        self._rates = list(rates)
        self._charges = {item.charge_id: item for item in charges}
        self._receipts = {item.payment_id: item for item in receipts}
        self._allocations = {item.allocation_id: item for item in allocations}
        self._waivers = {item.waiver_id: item for item in waivers}
        self._corrections = [dict(item) for item in corrections]
        for snapshot in closes:
            period_id = str(snapshot["period_id"])
            self._closed[period_id] = dict(snapshot)
            self._windows[period_id] = (as_date(snapshot["opens_on"]), as_date(snapshot["closes_on"]))

    # ------------------------------------------------------------------ rates
    def record_rate(self, base: str, quote: str, rate: Any, rate_date: Any,
                    source: str = "manual") -> FxRate:
        candidate = FxRate(base, quote, _decimal(rate, "rate"), as_date(rate_date, "rate date"), str(source))
        for existing in self._rates:
            if (existing.base, existing.quote, existing.rate_date) == (
                    candidate.base, candidate.quote, candidate.rate_date):
                if existing.rate == candidate.rate and existing.source == candidate.source:
                    return existing
                raise ReconciliationError(
                    f"cannot rewrite historical FX rate {candidate.base}/{candidate.quote} "
                    f"dated {_iso(candidate.rate_date)}")
        for closed_id, window in self._windows.items():
            if candidate.rate_date <= window[1]:
                raise ReconciliationError(
                    f"cannot insert FX rate dated {_iso(candidate.rate_date)}: closed period {closed_id} "
                    "history is immutable")
        self._rates.append(candidate)
        return candidate

    def rate_on(self, base: str, quote: str, when: Any) -> FxRate:
        base = _currency(base, "base currency")
        quote = _currency(quote, "quote currency")
        on = as_date(when, "rate date")
        if base == quote:
            return FxRate(base, quote, IDENTITY, on, "identity")
        candidates = [item for item in self._rates
                      if item.base == base and item.quote == quote and item.rate_date <= on]
        if not candidates:
            raise ReconciliationError(
                f"no {base}/{quote} FX rate on or before {_iso(on)}; record the rate before posting the payment")
        return max(candidates, key=lambda item: item.rate_date)

    # ------------------------------------------------------------------ bills
    def record_charge(self, charge_id: str, member_id: str, period_id: str, currency: str, amount: Any,
                      issued_on: Any, reference_rate_date: Any, entitlement_units: Any = 0,
                      record_id: str = "") -> Charge:
        candidate = Charge(charge_id, member_id, period_id, currency, _decimal(amount, "charge amount"),
                           as_date(issued_on, "issued_on"), as_date(reference_rate_date, "reference rate date"),
                           _decimal(entitlement_units, "entitlement units"), str(record_id or ""))
        if candidate.currency != self.settlement_currency:
            raise ReconciliationError(
                f"charge {candidate.charge_id} currency {candidate.currency} does not match settlement "
                f"currency {self.settlement_currency}")
        existing = self._charges.get(candidate.charge_id)
        if existing is not None:
            if existing.as_dict() == candidate.as_dict():
                return existing
            if candidate.period_id in self._closed:
                raise ReconciliationError(
                    f"closed period {candidate.period_id} bills are immutable and cannot be rewritten")
            raise ReconciliationError(f"charge {candidate.charge_id} already exists with different terms")
        self._charges[candidate.charge_id] = candidate
        return candidate

    def amend_charge(self, charge_id: str, *, amount: Any | None = None,
                     entitlement_units: Any | None = None, reason: str = "") -> Charge:
        existing = self._charges.get(charge_id)
        if existing is None:
            raise ReconciliationError(f"unknown charge {charge_id}")
        if existing.period_id in self._closed:
            raise ReconciliationError(
                f"closed period {existing.period_id} bills are immutable; record a correction instead")
        candidate = Charge(existing.charge_id, existing.member_id, existing.period_id, existing.currency,
                           existing.amount if amount is None else _decimal(amount, "charge amount"),
                           existing.issued_on, existing.reference_rate_date,
                           existing.entitlement_units if entitlement_units is None
                           else _decimal(entitlement_units, "entitlement units"),
                           existing.record_id, existing.version + 1)
        if candidate.as_dict() == existing.as_dict():
            return existing
        self._charges[charge_id] = candidate
        self._append_correction(self._correction(
            existing.period_id, existing.period_id, "charge_amended", charge_id, reason,
            {"before": existing.as_dict(), "after": candidate.as_dict()}))
        return candidate

    # --------------------------------------------------------------- receipts
    def post_receipt(self, payment_id: str, member_id: str, original_currency: str, original_amount: Any,
                     settlement_currency: str, paid_on: Any, *, rate_date: Any | None = None,
                     reference: str = "", correction_period_id: str | None = None,
                     reason: str = "") -> Receipt:
        original_currency = _currency(original_currency, "original currency")
        settlement_currency = _currency(settlement_currency, "settlement currency")
        if settlement_currency != self.settlement_currency:
            raise ReconciliationError(
                f"receipt settlement currency {settlement_currency} does not match book currency "
                f"{self.settlement_currency}")
        paid = as_date(paid_on, "paid_on")
        rate_on_date = paid if rate_date is None else as_date(rate_date, "rate date")
        applied = self.rate_on(original_currency, settlement_currency, rate_on_date)
        local_amount = money(original_amount, "original amount")
        settlement_value = money(local_amount * applied.rate, "settlement value")
        closed_period = self.period_for_date(paid)
        correction_period = str(correction_period_id or "")
        candidate = Receipt(payment_id, member_id, original_currency, local_amount, settlement_currency,
                            paid, rate_on_date, applied.rate, settlement_value, str(reference or ""),
                            closed_period or "", correction_period)
        existing = self._receipts.get(candidate.payment_id)
        if existing is not None:
            if self._receipt_identity(existing) == self._receipt_identity(candidate):
                return existing
            raise ReconciliationError(
                f"payment {candidate.payment_id} already exists with different terms; "
                "reverse it before posting a correction")
        if closed_period and not correction_period:
            raise ReconciliationError(
                f"payment dated {_iso(paid)} falls in closed period {closed_period}; "
                "post it through a correction period instead of rewriting the closed period")
        if closed_period and correction_period == closed_period:
            raise ReconciliationError("a correction cannot reuse the closed period identifier")
        self._receipts[candidate.payment_id] = candidate
        if closed_period:
            self._append_correction(self._correction(
                closed_period, correction_period, "late_receipt", candidate.payment_id, reason,
                {"paid_on": _iso(paid), "settlement_value": _s(settlement_value),
                 "rate_date": _iso(rate_on_date), "applied_rate": _s(applied.rate)}))
        return candidate

    @staticmethod
    def _receipt_identity(receipt: Receipt) -> dict[str, Any]:
        return {"member_id": receipt.member_id, "original_currency": receipt.original_currency,
                "original_amount": _s(receipt.original_amount),
                "settlement_currency": receipt.settlement_currency, "paid_on": _iso(receipt.paid_on),
                "rate_date": _iso(receipt.rate_date), "applied_rate": _s(receipt.applied_rate),
                "settlement_value": _s(receipt.settlement_value),
                "original_period_id": receipt.original_period_id,
                "correction_period_id": receipt.correction_period_id}

    def reverse_receipt(self, payment_id: str, reason: str = "",
                        correction_period_id: str | None = None) -> Receipt:
        receipt = self._receipts.get(payment_id)
        if receipt is None:
            raise ReconciliationError(f"unknown payment {payment_id}")
        if receipt.reversed:
            return receipt
        if self._active_allocations(payment_id=payment_id):
            raise ReconciliationError("reverse the payment allocations before reversing the receipt")
        period = receipt.original_period_id or self.period_for_date(receipt.paid_on) or ""
        correction = str(correction_period_id or receipt.correction_period_id or "")
        if period in self._closed and not correction:
            raise ReconciliationError(
                f"period {period} is closed; reverse the payment through a correction period")
        replacement = Receipt(**{**receipt.__dict__, "reversed": True})
        self._receipts[payment_id] = replacement
        if period in self._closed:
            self._append_correction(self._correction(
                period, correction, "receipt_reversed", payment_id, reason,
                {"settlement_value": _s(receipt.settlement_value)}))
        return replacement

    # ------------------------------------------------------------ allocations
    def allocate(self, payment_id: str, charge_id: str, amount: Any | None = None, *,
                 correction_period_id: str | None = None, reason: str = "") -> Allocation:
        receipt = self._receipts.get(payment_id)
        if receipt is None:
            raise ReconciliationError(f"unknown payment {payment_id}")
        charge = self._charges.get(charge_id)
        if charge is None:
            raise ReconciliationError(f"unknown charge {charge_id}")
        if receipt.reversed:
            raise ReconciliationError(f"payment {payment_id} has been reversed")
        if charge.currency != receipt.settlement_currency:
            raise ReconciliationError(
                f"charge {charge_id} is in {charge.currency} but payment {payment_id} settles in "
                f"{receipt.settlement_currency}")
        allocation_id = stable_hash({"payment_id": payment_id, "charge_id": charge_id})[:32]
        existing = self._allocations.get(allocation_id)
        if existing is not None and not existing.reversed:
            if amount is None or money(amount, "allocation amount") == existing.amount:
                return existing
            raise ReconciliationError(
                f"payment {payment_id} is already allocated to charge {charge_id} for "
                f"{_s(existing.amount)}; reverse that allocation before re-allocating")
        receipt_remaining = receipt.settlement_value - sum(
            item.amount for item in self._active_allocations(payment_id=payment_id))
        charge_remaining = self._charge_remaining(charge)
        if receipt_remaining <= 0:
            raise ReconciliationError(f"payment {payment_id} has no unapplied settlement value left")
        if charge_remaining <= 0:
            raise ReconciliationError(f"charge {charge_id} is already fully funded")
        requested = money(min(receipt_remaining, charge_remaining) if amount is None else amount,
                          "allocation amount")
        if requested <= 0:
            raise ReconciliationError("allocation amount must be positive")
        if requested > receipt_remaining:
            raise ReconciliationError(
                f"allocation exceeds remaining payment value ({_s(receipt_remaining)} {receipt.settlement_currency})")
        if requested > charge_remaining:
            raise ReconciliationError(
                f"allocation exceeds remaining charge balance ({_s(charge_remaining)} {charge.currency})")
        closed_period = self._closed_period_for_charge(charge)
        correction = str(correction_period_id or "")
        if closed_period and not correction:
            raise ReconciliationError(
                f"charge {charge_id} belongs to closed period {closed_period}; "
                "late corrections must allocate through a correction period")
        if closed_period and correction == closed_period:
            raise ReconciliationError("a correction cannot reuse the closed period identifier")
        if existing is not None and existing.reversed:
            allocation_id = stable_hash({"payment_id": payment_id, "charge_id": charge_id,
                                         "revision": len(self._allocations)})[:32]
        candidate = Allocation(allocation_id, payment_id, charge_id, requested, receipt.applied_rate,
                               receipt.rate_date, correction)
        self._allocations[allocation_id] = candidate
        if closed_period:
            self._append_correction(self._correction(
                closed_period, correction, "late_allocation", allocation_id, reason,
                {"payment_id": payment_id, "charge_id": charge_id, "amount": _s(requested),
                 "rate_date": _iso(receipt.rate_date), "applied_rate": _s(receipt.applied_rate)}))
        return candidate

    def reverse_allocation(self, allocation_id: str, reason: str = "",
                           correction_period_id: str | None = None) -> Allocation:
        allocation = self._allocations.get(allocation_id)
        if allocation is None:
            raise ReconciliationError(f"unknown allocation {allocation_id}")
        if allocation.reversed:
            return allocation
        charge = self._charges.get(allocation.charge_id)
        closed_period = self._closed_period_for_charge(charge) if charge else ""
        correction = str(correction_period_id or allocation.correction_period_id or "")
        if closed_period and not correction:
            raise ReconciliationError(
                f"charge {allocation.charge_id} belongs to closed period {closed_period}; "
                "reverse through a correction period")
        replacement = Allocation(**{**allocation.__dict__, "reversed": True})
        self._allocations[allocation_id] = replacement
        if closed_period:
            self._append_correction(self._correction(
                closed_period, correction, "allocation_reversed", allocation_id, reason,
                {"payment_id": allocation.payment_id, "charge_id": allocation.charge_id,
                 "amount": _s(allocation.amount)}))
        return replacement

    # ---------------------------------------------------------------- waivers
    def record_waiver(self, waiver_id: str, charge_id: str, currency: str, amount: Any, approved_on: Any,
                      reason: str = "", correction_period_id: str | None = None) -> Waiver:
        charge = self._charges.get(charge_id)
        if charge is None:
            raise ReconciliationError(f"unknown charge {charge_id}")
        if _currency(currency) != charge.currency:
            raise ReconciliationError(
                f"waiver currency {_currency(currency)} does not match charge currency {charge.currency}")
        value = money(amount, "waiver amount")
        existing = self._waivers.get(str(waiver_id))
        if existing is not None:
            if existing.as_dict() == Waiver(waiver_id, charge_id, currency, value,
                                            as_date(approved_on, "approved_on"), reason,
                                            str(correction_period_id or ""), False).as_dict():
                return existing
            raise ReconciliationError(f"waiver {waiver_id} already exists with different terms")
        active_waivers = sum(item.amount for item in self._waivers.values()
                             if item.charge_id == charge_id and not item.reversed)
        settled = sum(item.amount for item in self._active_allocations(charge_id=charge_id))
        if value + active_waivers + settled > charge.amount:
            raise ReconciliationError(
                f"waiver plus receipts would exceed charge {charge_id} amount {_s(charge.amount)}")
        closed_period = self._closed_period_for_charge(charge)
        correction = str(correction_period_id or "")
        if closed_period and not correction:
            raise ReconciliationError(
                f"charge {charge_id} belongs to closed period {closed_period}; "
                "record the waiver through a correction period")
        if closed_period and correction == closed_period:
            raise ReconciliationError("a correction cannot reuse the closed period identifier")
        candidate = Waiver(waiver_id, charge_id, charge.currency, value, as_date(approved_on, "approved_on"),
                           str(reason or ""), correction)
        self._waivers[candidate.waiver_id] = candidate
        if closed_period:
            self._append_correction(self._correction(
                closed_period, correction, "late_waiver", candidate.waiver_id, reason,
                {"charge_id": charge_id, "amount": _s(value)}))
        return candidate

    def reverse_waiver(self, waiver_id: str, reason: str = "",
                       correction_period_id: str | None = None) -> Waiver:
        waiver = self._waivers.get(waiver_id)
        if waiver is None:
            raise ReconciliationError(f"unknown waiver {waiver_id}")
        if waiver.reversed:
            return waiver
        charge = self._charges.get(waiver.charge_id)
        closed_period = self._closed_period_for_charge(charge) if charge else ""
        correction = str(correction_period_id or waiver.correction_period_id or "")
        if closed_period and not correction:
            raise ReconciliationError(
                f"charge {waiver.charge_id} belongs to closed period {closed_period}; "
                "reverse the waiver through a correction period")
        replacement = Waiver(**{**waiver.__dict__, "reversed": True})
        self._waivers[waiver_id] = replacement
        if closed_period:
            self._append_correction(self._correction(
                closed_period, correction, "waiver_reversed", waiver_id, reason,
                {"charge_id": waiver.charge_id, "amount": _s(waiver.amount)}))
        return replacement

    # -------------------------------------------------------- reconciliation
    def allocation_split(self, allocation: Allocation) -> tuple[Decimal, Decimal, Decimal]:
        """Split one allocation into (cash applied, reference-rate value, FX variance).

        ``cash`` is the settlement-currency amount actually credited. ``reference``
        restates the same original-currency portion at the bill's reference rate
        date, and ``fx`` is the difference. By construction ``cash == reference + fx``.
        """
        receipt = self._receipts.get(allocation.payment_id)
        charge = self._charges.get(allocation.charge_id)
        if receipt is None or charge is None:
            raise ReconciliationError("allocation references an unknown payment or charge")
        cash = allocation.amount
        if receipt.original_currency == charge.currency:
            return cash, cash, Decimal("0.00")
        reference = self.rate_on(receipt.original_currency, charge.currency, charge.reference_rate_date)
        original_portion = cash / allocation.rate
        reference_value = (original_portion * reference.rate).quantize(
            SETTLEMENT_SCALE, rounding=ROUND_HALF_UP)
        return cash, reference_value, (cash - reference_value).quantize(SETTLEMENT_SCALE)

    def fx_variance_for(self, allocation: Allocation) -> Decimal:
        return self.allocation_split(allocation)[2]

    def reconcile_charge(self, charge_id: str) -> ChargeReconciliation:
        charge = self._charges.get(charge_id)
        if charge is None:
            raise ReconciliationError(f"unknown charge {charge_id}")
        allocations = self._active_allocations(charge_id=charge_id)
        splits = [self.allocation_split(item) for item in allocations]
        cash = sum((item[0] for item in splits), Decimal("0.00")).quantize(SETTLEMENT_SCALE)
        reference_value = sum((item[1] for item in splits), Decimal("0.00")).quantize(SETTLEMENT_SCALE)
        fx_variance = sum((item[2] for item in splits), Decimal("0.00")).quantize(SETTLEMENT_SCALE)
        waiver_amount = sum((item.amount for item in self._waivers.values()
                             if item.charge_id == charge_id and not item.reversed),
                            Decimal("0.00")).quantize(SETTLEMENT_SCALE)
        residual = (charge.amount - cash - waiver_amount).quantize(SETTLEMENT_SCALE)
        outstanding = max(Decimal("0.00"), residual)
        credit = max(Decimal("0.00"), -residual)
        covered = charge.amount - outstanding
        ratio = (covered / charge.amount) if charge.amount > 0 else IDENTITY
        ratio = min(IDENTITY, max(Decimal("0.00"), ratio)).quantize(UNIT_SCALE, rounding=ROUND_HALF_UP)
        releasable = (charge.entitlement_units * ratio).quantize(UNIT_SCALE, rounding=ROUND_HALF_UP)
        return ChargeReconciliation(
            charge.charge_id, charge.member_id, charge.period_id, charge.currency, charge.amount,
            reference_value, fx_variance, waiver_amount, outstanding, credit,
            charge.entitlement_units, releasable, ratio, cash,
            tuple(sorted(item.allocation_id for item in allocations)),
            tuple(item.correction_period_id for item in allocations if item.correction_period_id))

    def reconcile(self) -> dict[str, Any]:
        rows = [self.reconcile_charge(item.charge_id) for item in self._charges.values()]
        totals = {
            "charged": sum((row.charged for row in rows), Decimal("0.00")),
            "receipts_settled": sum((row.receipts_settled for row in rows), Decimal("0.00")),
            "receipts_cash_applied": sum((row.receipts_cash_applied for row in rows), Decimal("0.00")),
            "fx_variance": sum((row.fx_variance for row in rows), Decimal("0.00")),
            "waiver_amount": sum((row.waiver_amount for row in rows), Decimal("0.00")),
            "outstanding_amount": sum((row.outstanding_amount for row in rows), Decimal("0.00")),
            "overpayment_credit": sum((row.overpayment_credit for row in rows), Decimal("0.00")),
            "entitlement_units": sum((row.entitlement_units for row in rows), Decimal("0.0000")),
            "releasable_units": sum((row.releasable_units for row in rows), Decimal("0.0000")),
        }
        explained = (totals["receipts_settled"] + totals["fx_variance"] + totals["waiver_amount"]
                     + totals["outstanding_amount"] - totals["overpayment_credit"])
        totals["explained_amount"] = explained
        totals["identity_holds"] = explained == totals["charged"]
        totals["coverage_ratio"] = (
            ((totals["charged"] - totals["outstanding_amount"]) / totals["charged"]).quantize(
                UNIT_SCALE, rounding=ROUND_HALF_UP) if totals["charged"] > 0 else IDENTITY)
        return {"settlement_currency": self.settlement_currency,
                "charges": [row.as_dict() for row in rows],
                "totals": {key: (_s(value) if isinstance(value, Decimal) else value)
                           for key, value in totals.items()},
                "unapplied_receipts": self.unapplied_receipts(),
                "corrections": [dict(item) for item in self._corrections],
                "closed_periods": self.period_summaries()}

    def unapplied_receipts(self) -> list[dict[str, Any]]:
        rows = []
        for receipt in self._receipts.values():
            if receipt.reversed:
                continue
            applied = sum((item.amount for item in self._active_allocations(payment_id=receipt.payment_id)),
                          Decimal("0.00"))
            remainder = receipt.settlement_value - applied
            if remainder > 0:
                rows.append({**receipt.as_dict(), "applied_settlement": _s(applied.quantize(SETTLEMENT_SCALE)),
                             "unapplied_settlement": _s(remainder.quantize(SETTLEMENT_SCALE))})
        return rows

    def release_report(self) -> dict[str, Any]:
        report = self.reconcile()
        report["explanation"] = self.explain_release()
        return report

    def explain_release(self) -> list[dict[str, Any]]:
        rows = []
        for charge in self._charges.values():
            item = self.reconcile_charge(charge.charge_id)
            rows.append({
                "charge_id": item.charge_id,
                "member_id": item.member_id,
                "period_id": item.period_id,
                "currency": item.currency,
                "equation": (
                    f"{_s(item.charged)} charged = {_s(item.receipts_settled)} receipts at reference rate "
                    f"+ {_s(item.fx_variance)} fx variance + {_s(item.waiver_amount)} waivers "
                    f"+ {_s(item.outstanding_amount)} outstanding "
                    f"- {_s(item.overpayment_credit)} overpayment credit"),
                "receipts_cash_applied": _s(item.receipts_cash_applied),
                "identity_holds": item.identity_holds,
                "entitlement_units": _s(item.entitlement_units),
                "releasable_units": _s(item.releasable_units),
                "coverage_ratio": _s(item.coverage_ratio),
                "withheld_units": _s((item.entitlement_units - item.releasable_units)
                                     .quantize(UNIT_SCALE, rounding=ROUND_HALF_UP)),
            })
        return rows

    # ---------------------------------------------------------------- closing
    def period_for_date(self, when: Any) -> str:
        on = as_date(when, "date")
        matches = [(period_id, window) for period_id, window in self._windows.items()
                   if window[0] <= on <= window[1]]
        if not matches:
            return ""
        return max(matches, key=lambda item: item[1][1])[0]

    def is_closed(self, period_id: str) -> bool:
        return period_id in self._closed

    def period_summaries(self) -> list[dict[str, Any]]:
        return [{"period_id": period_id, "closed_at": snapshot["closed_at"],
                 "opens_on": snapshot["opens_on"], "closes_on": snapshot["closes_on"],
                 "snapshot_hash": snapshot["snapshot_hash"]}
                for period_id, snapshot in self._closed.items()]

    def period_snapshot(self, period_id: str) -> dict[str, Any]:
        """Return the frozen close snapshot for a closed period, rehashed to its stored content."""
        snapshot = self._closed.get(period_id)
        if snapshot is None:
            raise ReconciliationError(f"period {period_id} is not closed")
        return dict(snapshot)

    def closed_period_snapshots(self) -> list[dict[str, Any]]:
        return [dict(snapshot) for snapshot in self._closed.values()]

    def close_period(self, period_id: str, closes_on: Any, *, opens_on: Any | None = None,
                     settlement_currency: str | None = None) -> dict[str, Any]:
        period_id = str(period_id or "").strip()
        if not period_id:
            raise ReconciliationError("period_id is required")
        closes = as_date(closes_on, "closes_on")
        if settlement_currency and _currency(settlement_currency) != self.settlement_currency:
            raise ReconciliationError(
                f"period settlement currency {_currency(settlement_currency)} does not match book currency "
                f"{self.settlement_currency}")
        if period_id in self._closed:
            existing = self._closed[period_id]
            if existing["closes_on"] == _iso(closes):
                return existing
            raise ReconciliationError(
                f"period {period_id} is already closed and its history cannot be rewritten")
        for closed_id, window in self._windows.items():
            if closes <= window[1]:
                raise ReconciliationError(
                    f"period {period_id} must close after already-closed period {closed_id} "
                    f"({_iso(window[1])})")
        if opens_on is None:
            opens = (max((window[1] for window in self._windows.values()), default=None))
            opens = (opens + timedelta(days=1)) if opens else date.min
        else:
            opens = as_date(opens_on, "opens_on")
        if opens > closes:
            raise ReconciliationError("opens_on cannot be after closes_on")

        charges = [item for item in self._charges.values() if item.period_id == period_id]
        charge_ids = {item.charge_id for item in charges}
        reconciliations = [self.reconcile_charge(item.charge_id) for item in charges]
        receipts = [item for item in self._receipts.values()
                    if opens <= item.paid_on <= closes and not item.reversed]
        allocations = [item for item in self._allocations.values() if item.charge_id in charge_ids]
        waivers = [item for item in self._waivers.values() if item.charge_id in charge_ids]
        rates = [item for item in self._rates if item.rate_date <= closes]
        body = {
            "period_id": period_id,
            "opens_on": _iso(opens),
            "closes_on": _iso(closes),
            "settlement_currency": self.settlement_currency,
            "closed_at": utc_now(),
            "rates": [item.as_dict() for item in rates],
            "bills": [item.as_dict() for item in charges],
            "receipts": [item.as_dict() for item in receipts],
            "allocations": [item.as_dict() for item in allocations],
            "waivers": [item.as_dict() for item in waivers],
            "reconciliations": [item.as_dict() for item in reconciliations],
        }
        body["snapshot_hash"] = stable_hash(body)
        self._closed[period_id] = body
        self._windows[period_id] = (opens, closes)
        return body

    def period_report(self, period_id: str) -> dict[str, Any]:
        period_id = str(period_id or "").strip()
        if period_id in self._closed:
            snapshot = self._closed[period_id]
            return {"period_id": period_id, "closed": True, "immutable": True,
                    "snapshot": snapshot,
                    "reconciliations": snapshot["reconciliations"],
                    "corrections": [dict(item) for item in self._corrections
                                    if item["period_id"] == period_id]}
        charges = [item for item in self._charges.values() if item.period_id == period_id]
        if not charges:
            raise ReconciliationError(f"unknown period {period_id}")
        return {"period_id": period_id, "closed": False, "immutable": False,
                "reconciliations": [self.reconcile_charge(item.charge_id).as_dict() for item in charges],
                "corrections": [dict(item) for item in self._corrections if item["period_id"] == period_id]}

    # --------------------------------------------------------------- internals
    def _active_allocations(self, *, payment_id: str | None = None,
                            charge_id: str | None = None) -> list[Allocation]:
        return [item for item in self._allocations.values()
                if not item.reversed
                and (payment_id is None or item.payment_id == payment_id)
                and (charge_id is None or item.charge_id == charge_id)]

    def _charge_remaining(self, charge: Charge) -> Decimal:
        settled = sum((item.amount for item in self._active_allocations(charge_id=charge.charge_id)),
                      Decimal("0.00"))
        waived = sum((item.amount for item in self._waivers.values()
                      if item.charge_id == charge.charge_id and not item.reversed), Decimal("0.00"))
        return (charge.amount - settled - waived).quantize(SETTLEMENT_SCALE)

    def _closed_period_for_charge(self, charge: Charge | None) -> str:
        if charge is None:
            return ""
        if charge.period_id in self._closed:
            return charge.period_id
        return self.period_for_date(charge.issued_on)

    def _correction(self, period_id: str, correction_period_id: str, kind: str, subject_id: str,
                    reason: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        correction_period = correction_period_id or f"{period_id}-CORR-{self._correction_sequence(period_id) + 1}"
        record = {"correction_id": stable_hash({"period_id": period_id, "kind": kind,
                                                "subject_id": subject_id,
                                                "payload": dict(payload)})[:32],
                  "period_id": period_id, "correction_period_id": correction_period,
                  "kind": kind, "subject_id": subject_id, "reason": str(reason or ""),
                  "payload": dict(payload), "created_at": utc_now()}
        return record

    def _append_correction(self, record: dict[str, Any]) -> dict[str, Any]:
        if not any(item["correction_id"] == record["correction_id"] for item in self._corrections):
            self._corrections.append(record)
        return record

    def _correction_sequence(self, period_id: str) -> int:
        return sum(1 for item in self._corrections if item["period_id"] == period_id)
