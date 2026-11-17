from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from member_settlement.accounts.member import ContractError, Decision, DomainRecord, records_from_fixture, stable_hash
from member_settlement.ledger.settlement_store import Repository
from member_settlement.periods.closing import advance_for_outcome, decide
from member_settlement.entitlements.release_report import export_bundle, verify_bundle
from member_settlement.payments.payment_allocation import derive_context
from member_settlement.payments.reconciliation import ReconciliationBook, ReconciliationError

from member_settlement.settlement_signal.settlement_health import augment_context

SETTLEMENT_CURRENCY = "USD"


class Application:
    def __init__(self, database: str | Path, context: Mapping[str, Any] | None = None,
                 settlement_currency: str = SETTLEMENT_CURRENCY):
        self.repository = Repository(database)
        self.context = dict(context or {})
        self.settlement_currency = settlement_currency

    @property
    def book(self) -> ReconciliationBook:
        return self.repository.load_reconciliation_book(self.settlement_currency)

    def ingest(self, record: DomainRecord) -> DomainRecord:
        current = self.repository.get_record(record.record_id)
        if current is None:
            self.repository.save_record(record)
            return record
        if current.fingerprint == record.fingerprint:
            return current
        replacement = DomainRecord(record.record_id, record.payload, current.state,
                                   current.version + 1, record.occurred_at, record.source)
        self.repository.save_record(replacement, expected_version=current.version)
        return replacement

    def process(self, record: DomainRecord) -> tuple[DomainRecord, Decision]:
        stored = self.ingest(record)
        context = dict(self.context)
        context.update(derive_context(stored, self.repository))
        context.update(augment_context(stored, self.repository))
        decision = decide(stored, context)
        self.repository.save_decision(decision)
        advanced = advance_for_outcome(stored, decision)
        if advanced.fingerprint != stored.fingerprint:
            self.repository.save_record(advanced, expected_version=stored.version)
        return advanced, decision

    def apply_posting(self, book: ReconciliationBook, posting: Mapping[str, Any]) -> None:
        kind = str(posting.get("kind") or "").strip()
        if kind == "rate":
            book.record_rate(posting["base"], posting["quote"], posting["rate"], posting["rate_date"],
                             posting.get("source", "fixture"))
        elif kind == "charge":
            book.record_charge(posting["charge_id"], posting["member_id"], posting["period_id"],
                               posting.get("currency", self.settlement_currency), posting["amount"],
                               posting["issued_on"], posting.get("reference_rate_date", posting["issued_on"]),
                               posting.get("entitlement_units", 0), posting.get("record_id", ""))
        elif kind == "receipt":
            receipt = book.post_receipt(
                posting["payment_id"], posting["member_id"], posting["original_currency"],
                posting["original_amount"], posting.get("settlement_currency", self.settlement_currency),
                posting["paid_on"], rate_date=posting.get("rate_date"),
                reference=posting.get("reference", ""),
                correction_period_id=posting.get("correction_period_id"),
                reason=posting.get("reason", ""))
            if posting.get("charge_id"):
                book.allocate(receipt.payment_id, posting["charge_id"], posting.get("allocate_amount"),
                              correction_period_id=posting.get("correction_period_id"),
                              reason=posting.get("reason", ""))
        elif kind == "allocation":
            book.allocate(posting["payment_id"], posting["charge_id"], posting.get("amount"),
                          correction_period_id=posting.get("correction_period_id"),
                          reason=posting.get("reason", ""))
        elif kind == "waiver":
            book.record_waiver(posting["waiver_id"], posting["charge_id"],
                               posting.get("currency", self.settlement_currency), posting["amount"],
                               posting["approved_on"], posting.get("reason", ""),
                               posting.get("correction_period_id"))
        elif kind == "close":
            book.close_period(posting["period_id"], posting["closes_on"],
                              opens_on=posting.get("opens_on"),
                              settlement_currency=posting.get("settlement_currency"))
        elif kind == "reverse_receipt":
            book.reverse_receipt(posting["payment_id"], posting.get("reason", ""),
                                 posting.get("correction_period_id"))
        elif kind == "reverse_allocation":
            book.reverse_allocation(posting["allocation_id"], posting.get("reason", ""),
                                    posting.get("correction_period_id"))
        elif kind == "reverse_waiver":
            book.reverse_waiver(posting["waiver_id"], posting.get("reason", ""),
                                posting.get("correction_period_id"))
        else:
            raise ReconciliationError(f"unknown posting kind: {kind!r}")

    def run_fixture(self, fixture: Mapping[str, Any], output: str | Path) -> dict[str, Any]:
        records = records_from_fixture(fixture)
        fixture_hash = stable_hash(fixture)
        run_id = self.repository.begin_run(fixture_hash, len(records))
        completed = self.repository.completed_run(run_id)
        if completed is not None:
            return completed
        decisions: dict[str, Decision] = {}
        final_records: list[DomainRecord] = []
        for record in records:
            final_record, decision = self.process(record)
            final_records.append(final_record)
            decisions[record.record_id] = decision
        book = ReconciliationBook(str(fixture.get("settlement_currency") or self.settlement_currency))
        for posting in fixture.get("postings") or []:
            self.apply_posting(book, posting)
        reconciliation = book.release_report()
        self.repository.persist_reconciliation(book)
        snapshot = self.repository.snapshot()
        if snapshot["chain_errors"]:
            raise ContractError("audit chain verification failed")
        manifest = export_bundle(output, final_records, decisions, snapshot, self.repository.event_rows(),
                                 reconciliation=reconciliation)
        result = {"run_id": run_id, "fixture_hash": fixture_hash, "records": len(final_records),
                  "decisions": len(decisions), "manifest": manifest, "snapshot": snapshot,
                  "reconciliation": reconciliation["totals"],
                  "closed_periods": [item["period_id"] for item in reconciliation["closed_periods"]]}
        self.repository.finish_run(run_id, result)
        return result

    def close_period(self, period_id: str, closes_on: str, opens_on: str | None = None) -> dict[str, Any]:
        book = self.book
        book.close_period(period_id, closes_on, opens_on=opens_on)
        self.repository.persist_reconciliation(book)
        return book.period_report(period_id)

    def period_report(self, period_id: str) -> dict[str, Any]:
        return self.book.period_report(period_id)

    def release_report(self) -> dict[str, Any]:
        return self.book.release_report()

    def reconcile_charge(self, charge_id: str) -> dict[str, Any]:
        return self.book.reconcile_charge(charge_id).as_dict()

    def inspect(self) -> dict[str, Any]:
        return {"snapshot": self.repository.snapshot(),
                "records": [record.__dict__ for record in self.repository.list_records()],
                "decisions": self.repository.decision_rows(),
                "reconciliation": self.repository.load_reconciliation_book(
                    self.settlement_currency).reconcile()}


def load_fixture(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read fixture: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("fixture root must be an object")
    return value


def run(fixture_path: str | Path, database: str | Path, output: str | Path,
        context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return Application(database, context).run_fixture(load_fixture(fixture_path), output)


def verify(database: str | Path, output: str | Path) -> dict[str, Any]:
    repository = Repository(database)
    chain_errors = repository.verify_chain()
    bundle_errors = verify_bundle(output)
    reconciliation = repository.load_reconciliation_book(SETTLEMENT_CURRENCY)
    report = reconciliation.reconcile()
    reconciliation_errors = [] if report["totals"]["identity_holds"] else [
        "reconciliation totals do not balance"]
    for row in report["charges"]:
        if not row["identity_holds"]:
            reconciliation_errors.append(f"charge {row['charge_id']} reconciliation identity does not hold")
    closed_errors = []
    for snapshot in reconciliation.closed_period_snapshots():
        body = {key: value for key, value in snapshot.items() if key != "snapshot_hash"}
        if stable_hash(body) != snapshot["snapshot_hash"]:
            closed_errors.append(f"closed period {snapshot['period_id']} snapshot hash mismatch")
    return {"ok": not chain_errors and not bundle_errors and not reconciliation_errors and not closed_errors,
            "chain_errors": chain_errors, "bundle_errors": bundle_errors,
            "reconciliation_errors": reconciliation_errors, "closed_period_errors": closed_errors,
            "snapshot": repository.snapshot(), "reconciliation": report["totals"]}
