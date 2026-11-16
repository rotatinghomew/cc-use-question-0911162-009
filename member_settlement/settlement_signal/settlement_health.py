from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

@dataclass(frozen=True)
class DomainSignal:
    code: str
    score: float
    severity: str
    evidence: dict[str, Any]

def number(payload: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    try:
        value = float(payload.get(key, default))
    except (TypeError, ValueError):
        return default
    return default if value != value or value in (float('inf'), float('-inf')) else value

def ratio(payload: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    value = number(payload, key, default)
    if value > 1.0:
        value /= 100.0
    return max(0.0, min(1.0, value))

def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))

def settlement_health(payload:Mapping[str,Any])->DomainSignal:
    due=Decimal(str(payload.get('assessment_amount',0))); outstanding=Decimal(str(payload.get('outstanding_amount',0))); waiver=Decimal(str(payload.get('waiver_amount',0))); coverage=ratio(payload,'payment_coverage')
    paid=max(Decimal('0'), due * Decimal(str(coverage)) - outstanding); credit=Decimal('0')
    if due < 0 or paid < 0 or waiver < 0: return DomainSignal('settlement_health',0.0,'critical',{'invalid_amount':True})
    settled=min(due,paid+waiver+credit); coverage=float(settled/due) if due else 1.0; arrears=max(Decimal('0'),due-settled)
    service=min(1.0,number(payload,'service_cost')/max(1.0,number(payload,'entitlement_units',1))); rights=min(1.0,number(payload,'entitlement_units')/max(1.0,float(due)))
    score=clamp(coverage*.62+(1-abs(service-rights))*.28+(1-ratio(payload,'delinquency_risk'))*.10)
    severity='critical' if arrears>due*Decimal('.5') else 'warning' if arrears>0 else 'info'
    return DomainSignal('settlement_health',score,severity,{'coverage':coverage,'arrears':str(arrears),'service_entitlement_gap':abs(service-rights)})

def peer_distribution(records:Iterable[Any],group_field:str='member_group')->dict[str,Any]:
    rows=[settlement_health(getattr(r,'payload',r)) for r in records]
    arrears=sum(Decimal(s.evidence.get('arrears','0')) for s in rows)
    return {'count':len(rows),'arrears':str(arrears),'delinquent':sum(s.severity!='info' for s in rows)}

def augment_context(record:Any,repository:Any)->dict[str,Any]:
    signal=settlement_health(record.payload); peers=peer_distribution(repository.list_records())
    return {'domain_signal':signal.score,'domain_severity':signal.severity,'delinquent_members':peers['delinquent'],'portfolio_arrears':peers['arrears']}
