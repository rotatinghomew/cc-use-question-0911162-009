from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from member_settlement.finance_office import Application, run, verify
from member_settlement.accounts.member import ContractError
from member_settlement.payments.reconciliation import ReconciliationError


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog='member_settlement', description='人工智能合作项目会费与服务权益清算账本')
    commands = root.add_subparsers(dest="command", required=True)
    execute = commands.add_parser("run")
    execute.add_argument("--fixture", required=True)
    execute.add_argument("--database", required=True)
    execute.add_argument("--output", required=True)
    check = commands.add_parser("verify")
    check.add_argument("--database", required=True)
    check.add_argument("--output", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--database", required=True)
    report = commands.add_parser("reconcile")
    report.add_argument("--database", required=True)
    report.add_argument("--charge", default=None)
    close = commands.add_parser("close")
    close.add_argument("--database", required=True)
    close.add_argument("--period", required=True)
    close.add_argument("--closes-on", required=True)
    close.add_argument("--opens-on", default=None)
    period = commands.add_parser("period")
    period.add_argument("--database", required=True)
    period.add_argument("--period", required=True)
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "run":
            result = run(args.fixture, args.database, args.output)
        elif args.command == "verify":
            result = verify(args.database, args.output)
        elif args.command == "reconcile":
            application = Application(args.database)
            result = (application.reconcile_charge(args.charge) if args.charge
                      else application.release_report())
        elif args.command == "close":
            result = Application(args.database).close_period(args.period, args.closes_on, args.opens_on)
        elif args.command == "period":
            result = Application(args.database).period_report(args.period)
        else:
            result = Application(args.database).inspect()
    except (ContractError, ReconciliationError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
