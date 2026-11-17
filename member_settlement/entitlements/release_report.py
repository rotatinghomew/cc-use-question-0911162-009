from __future__ import annotations

import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Mapping

from member_settlement.accounts.member import Decision, DomainRecord, canonical_json, stable_hash, utc_now


def ensure_output(path: str | Path) -> Path:
    output = Path(path)
    output.mkdir(parents=True, exist_ok=True)
    return output


def write_json(path: Path, value: Any) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
    path.write_text(body + "\n", encoding="utf-8")
    return stable_hash(value)


def write_records(path: Path, records: Iterable[DomainRecord], decisions: Mapping[str, Decision]) -> int:
    rows = []
    for record in records:
        decision = decisions.get(record.record_id)
        rows.append({"record_id": record.record_id, "state": record.state, "version": record.version,
                     "source": record.source, "fingerprint": record.fingerprint,
                     "outcome": decision.outcome if decision else "", "score": decision.score if decision else ""})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "state", "version", "source", "fingerprint", "outcome", "score"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def write_rules(path: Path, decisions: Mapping[str, Decision]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "code", "passed", "score", "severity", "message"])
        writer.writeheader()
        for record_id, decision in sorted(decisions.items()):
            for result in decision.rule_results:
                writer.writerow({"record_id": record_id, "code": result.code, "passed": result.passed,
                                 "score": result.score, "severity": result.severity, "message": result.message})
                count += 1
    return count


def build_summary(records: list[DomainRecord], decisions: Mapping[str, Decision], snapshot: Mapping[str, Any]) -> dict[str, Any]:
    outcomes: dict[str, int] = {}
    for decision in decisions.values():
        outcomes[decision.outcome] = outcomes.get(decision.outcome, 0) + 1
    scores = [decision.score for decision in decisions.values()]
    return {"product": '人工智能合作项目会费与服务权益清算账本', "entity": 'member_account', "generated_at": utc_now(),
            "record_count": len(records), "decision_count": len(decisions), "outcomes": outcomes,
            "average_score": sum(scores) / len(scores) if scores else 0.0,
            "minimum_score": min(scores) if scores else 0.0, "maximum_score": max(scores) if scores else 0.0,
            "repository": snapshot}


def export_bundle(output: str | Path, records: list[DomainRecord], decisions: Mapping[str, Decision],
                  snapshot: Mapping[str, Any], events: list[dict[str, Any]],
                  reconciliation: Mapping[str, Any] | None = None) -> dict[str, Any]:
    root = ensure_output(output)
    summary = build_summary(records, decisions, snapshot)
    if reconciliation is not None:
        summary["reconciliation"] = {
            "settlement_currency": reconciliation.get("settlement_currency"),
            "totals": reconciliation.get("totals"),
            "closed_periods": reconciliation.get("closed_periods", []),
        }
    record_count = write_records(root / "records.csv", records, decisions)
    rule_count = write_rules(root / "rules.csv", decisions)
    files: dict[str, str] = {}
    files["summary.json"] = write_json(root / "summary.json", summary)
    files["decisions.json"] = write_json(root / "decisions.json",
                                         [value.as_dict() for _, value in sorted(decisions.items())])
    files["audit-events.json"] = write_json(root / "audit-events.json", events)
    if reconciliation is not None:
        files["reconciliation.json"] = write_json(root / "reconciliation.json", dict(reconciliation))
        files.update(write_reconciliation_csvs(root, reconciliation))
    manifest = {"files": files, "record_rows": record_count,
                "rule_rows": rule_count, "created_at": utc_now()}
    manifest["manifest_hash"] = stable_hash(manifest)
    write_json(root / "manifest.json", manifest)
    return manifest


RECONCILIATION_FIELDS = ["charge_id", "member_id", "period_id", "currency", "charged",
                         "receipts_settled", "receipts_cash_applied", "fx_variance", "waiver_amount",
                         "outstanding_amount", "overpayment_credit", "entitlement_units",
                         "releasable_units", "coverage_ratio", "identity_holds", "allocation_ids",
                         "correction_periods"]


def write_reconciliation_csvs(root: Path, reconciliation: Mapping[str, Any]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    rows = reconciliation.get("charges", [])
    path = root / "reconciliation.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RECONCILIATION_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: (";".join(row[key]) if isinstance(row.get(key), list) else row.get(key, ""))
                             for key in RECONCILIATION_FIELDS})
    hashes["reconciliation.csv"] = sha256_file(path)

    correction_fields = ["correction_id", "period_id", "correction_period_id", "kind", "subject_id", "reason"]
    path = root / "corrections.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=correction_fields)
        writer.writeheader()
        for row in reconciliation.get("corrections", []):
            writer.writerow({key: row.get(key, "") for key in correction_fields})
    hashes["corrections.csv"] = sha256_file(path)

    release_fields = ["charge_id", "member_id", "period_id", "currency", "entitlement_units",
                      "releasable_units", "withheld_units", "coverage_ratio", "receipts_cash_applied",
                      "identity_holds"]
    path = root / "release-explanations.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=release_fields)
        writer.writeheader()
        for row in reconciliation.get("explanation", []):
            writer.writerow({key: row.get(key, "") for key in release_fields})
    hashes["release-explanations.csv"] = sha256_file(path)
    return hashes


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_bundle(output: str | Path) -> list[str]:
    root = Path(output)
    errors: list[str] = []
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return ["manifest.json is missing"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_manifest_hash = manifest.pop("manifest_hash", "")
    if stable_hash(manifest) != expected_manifest_hash:
        errors.append("manifest hash mismatch")
    for name, expected in manifest.get("files", {}).items():
        path = root / name
        if not path.is_file():
            errors.append(f"{name} is missing")
            continue
        if path.suffix == ".csv":
            if sha256_file(path) != expected:
                errors.append(f"{name} hash mismatch")
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        if stable_hash(value) != expected:
            errors.append(f"{name} hash mismatch")
    if (root / "reconciliation.json").is_file():
        errors.extend(verify_reconciliation(root))
    return errors


def verify_reconciliation(root: Path) -> list[str]:
    errors: list[str] = []
    report = json.loads((root / "reconciliation.json").read_text(encoding="utf-8"))
    for row in report.get("charges", []):
        explained = (Decimal(str(row["receipts_settled"])) + Decimal(str(row["fx_variance"]))
                     + Decimal(str(row["waiver_amount"])) + Decimal(str(row["outstanding_amount"]))
                     - Decimal(str(row["overpayment_credit"])))
        if explained != Decimal(str(row["charged"])):
            errors.append(f"charge {row['charge_id']} reconciliation identity does not hold")
        if not row.get("identity_holds", False):
            errors.append(f"charge {row['charge_id']} is marked unreconciled")
        if Decimal(str(row["releasable_units"])) > Decimal(str(row["entitlement_units"])):
            errors.append(f"charge {row['charge_id']} releases more units than it grants")
    totals = report.get("totals", {})
    if not totals.get("identity_holds", False):
        errors.append("reconciliation totals do not balance")
    return errors
