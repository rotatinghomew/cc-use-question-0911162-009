from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from member_settlement.accounts.member import Decision, DomainRecord, ContractError, canonical_json, stable_hash, utc_now
from member_settlement.payments.reconciliation import (
    Allocation, Charge, FxRate, Receipt, ReconciliationBook, Waiver,
)


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS records(
    record_id TEXT PRIMARY KEY,
    version INTEGER NOT NULL,
    state TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    source TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS record_versions(
    record_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    state TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    stored_at TEXT NOT NULL,
    PRIMARY KEY(record_id, version)
);
CREATE TABLE IF NOT EXISTS decisions(
    decision_id TEXT PRIMARY KEY,
    record_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    score REAL NOT NULL,
    decision_json TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    FOREIGN KEY(record_id) REFERENCES records(record_id)
);
CREATE TABLE IF NOT EXISTS events(
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    aggregate_version INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    event_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    UNIQUE(aggregate_id, aggregate_version, event_type)
);
CREATE TABLE IF NOT EXISTS runs(
    run_id TEXT PRIMARY KEY,
    fixture_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    result_json TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT
);
CREATE TABLE IF NOT EXISTS fx_rates(
    base TEXT NOT NULL,
    quote TEXT NOT NULL,
    rate_date TEXT NOT NULL,
    rate_json TEXT NOT NULL,
    PRIMARY KEY(base, quote, rate_date)
);
CREATE TABLE IF NOT EXISTS charges(
    charge_id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL,
    period_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    charge_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS receipts(
    payment_id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL,
    original_period_id TEXT NOT NULL,
    correction_period_id TEXT NOT NULL,
    receipt_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS allocations(
    allocation_id TEXT PRIMARY KEY,
    payment_id TEXT NOT NULL,
    charge_id TEXT NOT NULL,
    correction_period_id TEXT NOT NULL,
    allocation_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS waivers(
    waiver_id TEXT PRIMARY KEY,
    charge_id TEXT NOT NULL,
    correction_period_id TEXT NOT NULL,
    waiver_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS period_closes(
    period_id TEXT PRIMARY KEY,
    closes_on TEXT NOT NULL,
    snapshot_json TEXT NOT NULL,
    snapshot_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS corrections(
    correction_id TEXT PRIMARY KEY,
    period_id TEXT NOT NULL,
    correction_period_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    correction_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_records_state ON records(state, updated_at);
CREATE INDEX IF NOT EXISTS idx_events_aggregate ON events(aggregate_id, event_id);
CREATE INDEX IF NOT EXISTS idx_decisions_record ON decisions(record_id, decided_at);
CREATE INDEX IF NOT EXISTS idx_charges_period ON charges(period_id, member_id);
CREATE INDEX IF NOT EXISTS idx_allocations_charge ON allocations(charge_id, payment_id);
CREATE INDEX IF NOT EXISTS idx_period_closes_date ON period_closes(closes_on);
"""


class Repository:
    def __init__(self, database: str | Path):
        self.database = str(database)
        self._lock = threading.RLock()
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=30000")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            connection = self.connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()

    def _last_hash(self, connection: sqlite3.Connection) -> str:
        row = connection.execute("SELECT event_hash FROM events ORDER BY event_id DESC LIMIT 1").fetchone()
        return row[0] if row else "0" * 64

    def append_event(self, connection: sqlite3.Connection, event_type: str,
                     aggregate_id: str, aggregate_version: int, payload: Mapping[str, Any]) -> str:
        previous = self._last_hash(connection)
        created_at = utc_now()
        event_hash = stable_hash({"event_type": event_type, "aggregate_id": aggregate_id,
                                  "aggregate_version": aggregate_version, "payload": payload,
                                  "previous_hash": previous, "created_at": created_at})
        try:
            connection.execute("INSERT INTO events(event_type,aggregate_id,aggregate_version,payload_json,previous_hash,event_hash,created_at) VALUES(?,?,?,?,?,?,?)",
                               (event_type, aggregate_id, aggregate_version, canonical_json(payload),
                                previous, event_hash, created_at))
        except sqlite3.IntegrityError:
            row = connection.execute("SELECT event_hash,payload_json FROM events WHERE aggregate_id=? AND aggregate_version=? AND event_type=?",
                                     (aggregate_id, aggregate_version, event_type)).fetchone()
            if row and row[1] == canonical_json(payload):
                return row[0]
            raise ContractError("conflicting event replay") from None
        return event_hash

    def save_record(self, record: DomainRecord, expected_version: int | None = None) -> str:
        with self.transaction() as connection:
            current = connection.execute("SELECT version,fingerprint FROM records WHERE record_id=?", (record.record_id,)).fetchone()
            if current and expected_version is not None and current[0] != expected_version:
                raise ContractError("optimistic version conflict")
            if current and current[1] == record.fingerprint:
                return record.fingerprint
            if current and record.version <= current[0]:
                raise ContractError("record version must advance")
            payload = canonical_json(record.payload)
            connection.execute("INSERT INTO records(record_id,version,state,payload_json,fingerprint,occurred_at,source,updated_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(record_id) DO UPDATE SET version=excluded.version,state=excluded.state,payload_json=excluded.payload_json,fingerprint=excluded.fingerprint,occurred_at=excluded.occurred_at,source=excluded.source,updated_at=excluded.updated_at",
                               (record.record_id, record.version, record.state, payload, record.fingerprint,
                                record.occurred_at, record.source, utc_now()))
            connection.execute("INSERT INTO record_versions(record_id,version,state,payload_json,fingerprint,stored_at) VALUES(?,?,?,?,?,?)",
                               (record.record_id, record.version, record.state, payload, record.fingerprint, utc_now()))
            self.append_event(connection, "record.saved", record.record_id, record.version,
                              {"state": record.state, "fingerprint": record.fingerprint})
            return record.fingerprint

    def get_record(self, record_id: str) -> DomainRecord | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM records WHERE record_id=?", (record_id,)).fetchone()
        if not row:
            return None
        return DomainRecord(record_id=row["record_id"], payload=json.loads(row["payload_json"]),
                            state=row["state"], version=row["version"], occurred_at=row["occurred_at"],
                            source=row["source"])

    def list_records(self, state: str | None = None) -> list[DomainRecord]:
        query = "SELECT * FROM records"
        params: tuple[Any, ...] = ()
        if state:
            query += " WHERE state=?"
            params = (state,)
        query += " ORDER BY record_id"
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [DomainRecord(record_id=row["record_id"], payload=json.loads(row["payload_json"]),
                             state=row["state"], version=row["version"], occurred_at=row["occurred_at"],
                             source=row["source"]) for row in rows]

    def save_decision(self, decision: Decision) -> str:
        decision_id = decision.fingerprint
        with self.transaction() as connection:
            if not connection.execute("SELECT 1 FROM records WHERE record_id=?", (decision.record_id,)).fetchone():
                raise ContractError("decision record does not exist")
            body = canonical_json(decision.as_dict())
            connection.execute("INSERT OR IGNORE INTO decisions(decision_id,record_id,outcome,score,decision_json,decided_at) VALUES(?,?,?,?,?,?)",
                               (decision_id, decision.record_id, decision.outcome, decision.score, body, decision.decided_at))
            self.append_event(connection, "decision.saved", decision.record_id,
                              self.event_count(decision.record_id, connection) + 1,
                              {"decision_id": decision_id, "outcome": decision.outcome, "score": decision.score})
        return decision_id

    def event_count(self, aggregate_id: str, connection: sqlite3.Connection | None = None) -> int:
        owns = connection is None
        connection = connection or self.connect()
        try:
            row = connection.execute("SELECT COUNT(*) FROM events WHERE aggregate_id=?", (aggregate_id,)).fetchone()
            return int(row[0])
        finally:
            if owns:
                connection.close()

    def begin_run(self, fixture_hash: str, record_count: int) -> str:
        run_id = stable_hash({"fixture_hash": fixture_hash, "record_count": record_count})[:24]
        with self.transaction() as connection:
            row = connection.execute("SELECT fixture_hash,record_count FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if row and (row[0] != fixture_hash or row[1] != record_count):
                raise ContractError("run identifier collision")
            connection.execute("INSERT OR IGNORE INTO runs(run_id,fixture_hash,status,record_count,result_json,started_at) VALUES(?,?,?,?,?,?)",
                               (run_id, fixture_hash, "running", record_count, "{}", utc_now()))
        return run_id

    def completed_run(self, run_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute("SELECT status,result_json FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if not row or row["status"] != "finished":
            return None
        result = json.loads(row["result_json"])
        if not isinstance(result, dict):
            raise ContractError("stored run result is invalid")
        return result

    def finish_run(self, run_id: str, result: Mapping[str, Any]) -> None:
        with self.transaction() as connection:
            changed = connection.execute("UPDATE runs SET status='finished',result_json=?,finished_at=? WHERE run_id=?",
                                         (canonical_json(result), utc_now(), run_id)).rowcount
            if changed != 1:
                raise ContractError("unknown run")
            self.append_event(connection, "run.finished", run_id, 1, dict(result))

    def verify_chain(self) -> list[str]:
        errors: list[str] = []
        previous = "0" * 64
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM events ORDER BY event_id").fetchall()
        for row in rows:
            payload = json.loads(row["payload_json"])
            expected = stable_hash({"event_type": row["event_type"], "aggregate_id": row["aggregate_id"],
                                    "aggregate_version": row["aggregate_version"], "payload": payload,
                                    "previous_hash": row["previous_hash"], "created_at": row["created_at"]})
            if row["previous_hash"] != previous:
                errors.append(f"event {row['event_id']} previous hash mismatch")
            if row["event_hash"] != expected:
                errors.append(f"event {row['event_id']} content hash mismatch")
            previous = row["event_hash"]
        return errors

    def snapshot(self) -> dict[str, Any]:
        with self.connect() as connection:
            counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                      for table in ("records", "record_versions", "decisions", "events", "runs",
                                    "fx_rates", "charges", "receipts", "allocations", "waivers",
                                    "period_closes", "corrections")}
            states = {row[0]: row[1] for row in connection.execute("SELECT state,COUNT(*) FROM records GROUP BY state")}
        return {"counts": counts, "states": states, "chain_errors": self.verify_chain()}

    def decision_rows(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT decision_json FROM decisions ORDER BY record_id,decided_at").fetchall()
        return [json.loads(row[0]) for row in rows]

    def event_rows(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM events ORDER BY event_id").fetchall()
        return [dict(row) | {"payload": json.loads(row["payload_json"])} for row in rows]

    # ------------------------------------------------------------ reconciliation
    def save_fx_rate(self, rate: FxRate) -> None:
        body = canonical_json(rate.as_dict())
        with self.transaction() as connection:
            existing = connection.execute(
                "SELECT rate_json FROM fx_rates WHERE base=? AND quote=? AND rate_date=?",
                (rate.base, rate.quote, rate.rate_date.isoformat())).fetchone()
            if existing and existing[0] != body:
                raise ContractError(
                    f"historical FX rate {rate.base}/{rate.quote} {rate.rate_date.isoformat()} is immutable")
            if existing:
                return
            latest = connection.execute(
                "SELECT MAX(closes_on) FROM period_closes WHERE closes_on >= ?",
                (rate.rate_date.isoformat(),)).fetchone()[0]
            if latest is not None:
                raise ContractError(
                    f"historical FX rate dated {rate.rate_date.isoformat()} is immutable: "
                    f"period closing {latest} already froze it")
            connection.execute(
                "INSERT INTO fx_rates(base,quote,rate_date,rate_json) VALUES(?,?,?,?)",
                (rate.base, rate.quote, rate.rate_date.isoformat(), body))
            sequence = connection.execute("SELECT COUNT(*) FROM events WHERE aggregate_id=?",
                                          (f"fx:{rate.base}/{rate.quote}",)).fetchone()[0]
            self.append_event(connection, "fx_rate.recorded", f"fx:{rate.base}/{rate.quote}",
                              sequence + 1, rate.as_dict())

    def save_charge(self, charge: Charge) -> None:
        body = canonical_json(charge.as_dict())
        with self.transaction() as connection:
            existing = connection.execute("SELECT version,charge_json FROM charges WHERE charge_id=?",
                                          (charge.charge_id,)).fetchone()
            if existing:
                if existing[1] == body:
                    return
                if charge.version <= existing[0]:
                    raise ContractError("charge version must advance")
            connection.execute(
                "INSERT INTO charges(charge_id,member_id,period_id,version,charge_json) VALUES(?,?,?,?,?) "
                "ON CONFLICT(charge_id) DO UPDATE SET member_id=excluded.member_id,"
                "period_id=excluded.period_id,version=excluded.version,charge_json=excluded.charge_json",
                (charge.charge_id, charge.member_id, charge.period_id, charge.version, body))
            self.append_event(connection, "charge.saved", charge.charge_id, charge.version, charge.as_dict())

    def save_receipt(self, receipt: Receipt) -> None:
        body = canonical_json(receipt.as_dict())
        with self.transaction() as connection:
            existing = connection.execute("SELECT receipt_json FROM receipts WHERE payment_id=?",
                                          (receipt.payment_id,)).fetchone()
            if existing:
                if existing[0] == body:
                    return
                if not receipt.reversed:
                    raise ContractError("a posted receipt cannot be rewritten; reverse it instead")
            connection.execute(
                "INSERT INTO receipts(payment_id,member_id,original_period_id,correction_period_id,receipt_json) "
                "VALUES(?,?,?,?,?) ON CONFLICT(payment_id) DO UPDATE SET member_id=excluded.member_id,"
                "original_period_id=excluded.original_period_id,"
                "correction_period_id=excluded.correction_period_id,receipt_json=excluded.receipt_json",
                (receipt.payment_id, receipt.member_id, receipt.original_period_id,
                 receipt.correction_period_id, body))
            sequence = connection.execute("SELECT COUNT(*) FROM events WHERE aggregate_id=?",
                                          (f"receipt:{receipt.payment_id}",)).fetchone()[0]
            self.append_event(connection, "receipt.saved", f"receipt:{receipt.payment_id}", sequence + 1,
                              receipt.as_dict())

    def save_allocation(self, allocation: Allocation) -> None:
        body = canonical_json(allocation.as_dict())
        with self.transaction() as connection:
            existing = connection.execute("SELECT allocation_json FROM allocations WHERE allocation_id=?",
                                          (allocation.allocation_id,)).fetchone()
            if existing:
                if existing[0] == body:
                    return
                if not allocation.reversed:
                    raise ContractError("a posted allocation cannot be rewritten; reverse it instead")
            connection.execute(
                "INSERT INTO allocations(allocation_id,payment_id,charge_id,correction_period_id,allocation_json) "
                "VALUES(?,?,?,?,?) ON CONFLICT(allocation_id) DO UPDATE SET "
                "payment_id=excluded.payment_id,charge_id=excluded.charge_id,"
                "correction_period_id=excluded.correction_period_id,allocation_json=excluded.allocation_json",
                (allocation.allocation_id, allocation.payment_id, allocation.charge_id,
                 allocation.correction_period_id, body))
            sequence = connection.execute("SELECT COUNT(*) FROM events WHERE aggregate_id=?",
                                          (f"allocation:{allocation.allocation_id}",)).fetchone()[0]
            self.append_event(connection, "allocation.saved", f"allocation:{allocation.allocation_id}",
                              sequence + 1, allocation.as_dict())

    def save_waiver(self, waiver: Waiver) -> None:
        body = canonical_json(waiver.as_dict())
        with self.transaction() as connection:
            existing = connection.execute("SELECT waiver_json FROM waivers WHERE waiver_id=?",
                                          (waiver.waiver_id,)).fetchone()
            if existing:
                if existing[0] == body:
                    return
                if not waiver.reversed:
                    raise ContractError("a posted waiver cannot be rewritten; reverse it instead")
            connection.execute(
                "INSERT INTO waivers(waiver_id,charge_id,correction_period_id,waiver_json) VALUES(?,?,?,?) "
                "ON CONFLICT(waiver_id) DO UPDATE SET charge_id=excluded.charge_id,"
                "correction_period_id=excluded.correction_period_id,waiver_json=excluded.waiver_json",
                (waiver.waiver_id, waiver.charge_id, waiver.correction_period_id, body))
            sequence = connection.execute("SELECT COUNT(*) FROM events WHERE aggregate_id=?",
                                          (f"waiver:{waiver.waiver_id}",)).fetchone()[0]
            self.append_event(connection, "waiver.saved", f"waiver:{waiver.waiver_id}", sequence + 1,
                              waiver.as_dict())

    def save_period_close(self, snapshot: Mapping[str, Any]) -> None:
        period_id = str(snapshot["period_id"])
        body = canonical_json(snapshot)
        snapshot_hash = str(snapshot["snapshot_hash"])
        with self.transaction() as connection:
            existing = connection.execute("SELECT snapshot_hash FROM period_closes WHERE period_id=?",
                                          (period_id,)).fetchone()
            if existing:
                if existing[0] == snapshot_hash:
                    return
                raise ContractError(f"closed period {period_id} history is immutable")
            connection.execute(
                "INSERT INTO period_closes(period_id,closes_on,snapshot_json,snapshot_hash) VALUES(?,?,?,?)",
                (period_id, str(snapshot["closes_on"]), body, snapshot_hash))
            self.append_event(connection, "period.closed", f"period:{period_id}", 1,
                              {"snapshot_hash": snapshot_hash, "closes_on": str(snapshot["closes_on"])})

    def save_correction(self, correction: Mapping[str, Any]) -> None:
        body = canonical_json(correction)
        with self.transaction() as connection:
            existing = connection.execute("SELECT correction_json FROM corrections WHERE correction_id=?",
                                          (correction["correction_id"],)).fetchone()
            if existing:
                if existing[0] == body:
                    return
                raise ContractError("correction history is immutable")
            connection.execute(
                "INSERT INTO corrections(correction_id,period_id,correction_period_id,kind,correction_json) "
                "VALUES(?,?,?,?,?)",
                (correction["correction_id"], correction["period_id"],
                 correction["correction_period_id"], correction["kind"], body))
            self.append_event(connection, "correction.recorded",
                              f"correction:{correction['correction_id']}", 1, dict(correction))

    def reconciliation_rows(self) -> dict[str, list[Any]]:
        with self.connect() as connection:
            rates = [FxRate(**json.loads(row[0])) for row in
                     connection.execute("SELECT rate_json FROM fx_rates ORDER BY base,quote,rate_date")]
            charges = [Charge(**json.loads(row[0])) for row in
                       connection.execute("SELECT charge_json FROM charges ORDER BY charge_id")]
            receipts = [Receipt(**json.loads(row[0])) for row in
                        connection.execute("SELECT receipt_json FROM receipts ORDER BY payment_id")]
            allocations = [Allocation(**json.loads(row[0])) for row in
                           connection.execute("SELECT allocation_json FROM allocations ORDER BY allocation_id")]
            waivers = [Waiver(**json.loads(row[0])) for row in
                       connection.execute("SELECT waiver_json FROM waivers ORDER BY waiver_id")]
            closes = [json.loads(row[0]) for row in
                      connection.execute("SELECT snapshot_json FROM period_closes ORDER BY closes_on")]
            corrections = [json.loads(row[0]) for row in
                           connection.execute("SELECT correction_json FROM corrections ORDER BY correction_id")]
        return {"rates": rates, "charges": charges, "receipts": receipts, "allocations": allocations,
                "waivers": waivers, "closes": closes, "corrections": corrections}

    def load_reconciliation_book(self, settlement_currency: str = "USD") -> ReconciliationBook:
        book = ReconciliationBook(settlement_currency)
        rows = self.reconciliation_rows()
        book.restore(rates=rows["rates"], charges=rows["charges"], receipts=rows["receipts"],
                     allocations=rows["allocations"], waivers=rows["waivers"],
                     corrections=rows["corrections"], closes=rows["closes"],
                     settlement_currency=settlement_currency)
        return book

    def persist_reconciliation(self, book: ReconciliationBook) -> None:
        for rate in book.rates:
            self.save_fx_rate(rate)
        for charge in book.charges:
            self.save_charge(charge)
        for receipt in book.receipts:
            self.save_receipt(receipt)
        for allocation in book.allocations:
            self.save_allocation(allocation)
        for waiver in book.waivers:
            self.save_waiver(waiver)
        for snapshot in book.closed_period_snapshots():
            self.save_period_close(snapshot)
        for correction in book.corrections:
            self.save_correction(correction)
