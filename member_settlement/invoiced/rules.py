from __future__ import annotations

import math
from typing import Any, Callable, Mapping

from member_settlement.accounts.member import DomainRecord, RuleResult, bounded, finite_number, normalized_text

RuleFunction = Callable[[DomainRecord, Mapping[str, Any]], RuleResult]

def _number(record: DomainRecord, field: str) -> float:
    value = record.payload.get(field)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return finite_number(value)
    text = normalized_text(value)
    if not text:
        return 0.0
    try:
        return finite_number(text)
    except ValueError:
        tokens = [item for item in text.replace(',', ' ').replace(';', ' ').split() if item]
        return float(min(100, len(text) + len(set(tokens)) * 5))

def _context_number(context: Mapping[str, Any], key: str, default: float) -> float:
    try:
        return finite_number(context.get(key, default))
    except ValueError:
        return default

def _result(code: str, value: float, threshold: float, higher_is_better: bool, message: str, evidence: dict[str, Any]) -> RuleResult:
    distance = (value - threshold) if higher_is_better else (threshold - value)
    passed = distance >= 0
    scale = max(1.0, abs(threshold))
    score = bounded(0.5 + distance / (2.0 * scale))
    severity = 'info' if passed else ('critical' if score < 0.2 else 'error')
    return RuleResult(code, passed, score, severity, message, evidence)

def check_member_category_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_category')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_member_category_presence_threshold', 10.333)
    return _result('check_member_category_presence', adjusted, threshold, True, 'validates member_category presence',
                   {'field': 'member_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_category_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_category')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_member_category_range_threshold', 12.667)
    return _result('check_member_category_range', adjusted, threshold, True, 'validates member_category range',
                   {'field': 'member_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_category_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_category')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_member_category_stability_threshold', 15.0)
    return _result('check_member_category_stability', adjusted, threshold, False, 'validates member_category stability',
                   {'field': 'member_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_category_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_category')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_member_category_freshness_threshold', 17.333)
    return _result('check_member_category_freshness', adjusted, threshold, True, 'validates member_category freshness',
                   {'field': 'member_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_category_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_category')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_member_category_coverage_threshold', 19.667)
    return _result('check_member_category_coverage', adjusted, threshold, True, 'validates member_category coverage',
                   {'field': 'member_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_category_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_category')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_member_category_consistency_threshold', 22.0)
    return _result('check_member_category_consistency', adjusted, threshold, False, 'validates member_category consistency',
                   {'field': 'member_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_category_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_category')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_member_category_risk_threshold', 24.333)
    return _result('check_member_category_risk', adjusted, threshold, True, 'validates member_category risk',
                   {'field': 'member_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_category_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_category')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_member_category_confidence_threshold', 26.667)
    return _result('check_member_category_confidence', adjusted, threshold, True, 'validates member_category confidence',
                   {'field': 'member_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_category_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_category')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_member_category_dependency_threshold', 29.0)
    return _result('check_member_category_dependency', adjusted, threshold, False, 'validates member_category dependency',
                   {'field': 'member_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_category_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_category')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_member_category_readiness_threshold', 31.333)
    return _result('check_member_category_readiness', adjusted, threshold, True, 'validates member_category readiness',
                   {'field': 'member_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_id_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_id')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_member_id_presence_threshold', 9.333)
    return _result('check_member_id_presence', adjusted, threshold, True, 'validates member_id presence',
                   {'field': 'member_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_id_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_id')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_member_id_range_threshold', 11.667)
    return _result('check_member_id_range', adjusted, threshold, False, 'validates member_id range',
                   {'field': 'member_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_id_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_id')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_member_id_stability_threshold', 14.0)
    return _result('check_member_id_stability', adjusted, threshold, True, 'validates member_id stability',
                   {'field': 'member_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_id_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_id')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_member_id_freshness_threshold', 16.333)
    return _result('check_member_id_freshness', adjusted, threshold, True, 'validates member_id freshness',
                   {'field': 'member_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_id_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_id')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_member_id_coverage_threshold', 18.667)
    return _result('check_member_id_coverage', adjusted, threshold, False, 'validates member_id coverage',
                   {'field': 'member_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_id_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_id')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_member_id_consistency_threshold', 21.0)
    return _result('check_member_id_consistency', adjusted, threshold, True, 'validates member_id consistency',
                   {'field': 'member_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_id_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_id')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_member_id_risk_threshold', 23.333)
    return _result('check_member_id_risk', adjusted, threshold, True, 'validates member_id risk',
                   {'field': 'member_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_id_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_id')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_member_id_confidence_threshold', 25.667)
    return _result('check_member_id_confidence', adjusted, threshold, False, 'validates member_id confidence',
                   {'field': 'member_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_id_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_id')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_member_id_dependency_threshold', 28.0)
    return _result('check_member_id_dependency', adjusted, threshold, True, 'validates member_id dependency',
                   {'field': 'member_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_member_id_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'member_id')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_member_id_readiness_threshold', 30.333)
    return _result('check_member_id_readiness', adjusted, threshold, True, 'validates member_id readiness',
                   {'field': 'member_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_basis_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_basis')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_assessment_basis_presence_threshold', 8.333)
    return _result('check_assessment_basis_presence', adjusted, threshold, False, 'validates assessment_basis presence',
                   {'field': 'assessment_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_basis_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_basis')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_assessment_basis_range_threshold', 10.667)
    return _result('check_assessment_basis_range', adjusted, threshold, True, 'validates assessment_basis range',
                   {'field': 'assessment_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_basis_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_basis')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_assessment_basis_stability_threshold', 13.0)
    return _result('check_assessment_basis_stability', adjusted, threshold, True, 'validates assessment_basis stability',
                   {'field': 'assessment_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_basis_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_basis')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_assessment_basis_freshness_threshold', 15.333)
    return _result('check_assessment_basis_freshness', adjusted, threshold, False, 'validates assessment_basis freshness',
                   {'field': 'assessment_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_basis_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_basis')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_assessment_basis_coverage_threshold', 17.667)
    return _result('check_assessment_basis_coverage', adjusted, threshold, True, 'validates assessment_basis coverage',
                   {'field': 'assessment_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_basis_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_basis')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_assessment_basis_consistency_threshold', 20.0)
    return _result('check_assessment_basis_consistency', adjusted, threshold, True, 'validates assessment_basis consistency',
                   {'field': 'assessment_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_basis_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_basis')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_assessment_basis_risk_threshold', 22.333)
    return _result('check_assessment_basis_risk', adjusted, threshold, False, 'validates assessment_basis risk',
                   {'field': 'assessment_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_basis_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_basis')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_assessment_basis_confidence_threshold', 24.667)
    return _result('check_assessment_basis_confidence', adjusted, threshold, True, 'validates assessment_basis confidence',
                   {'field': 'assessment_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_basis_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_basis')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_assessment_basis_dependency_threshold', 27.0)
    return _result('check_assessment_basis_dependency', adjusted, threshold, True, 'validates assessment_basis dependency',
                   {'field': 'assessment_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_basis_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_basis')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_assessment_basis_readiness_threshold', 29.333)
    return _result('check_assessment_basis_readiness', adjusted, threshold, False, 'validates assessment_basis readiness',
                   {'field': 'assessment_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_outstanding_amount_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'outstanding_amount')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_outstanding_amount_presence_threshold', 31.667)
    return _result('check_outstanding_amount_presence', adjusted, threshold, True, 'validates outstanding_amount presence',
                   {'field': 'outstanding_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_outstanding_amount_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'outstanding_amount')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_outstanding_amount_range_threshold', 9.667)
    return _result('check_outstanding_amount_range', adjusted, threshold, True, 'validates outstanding_amount range',
                   {'field': 'outstanding_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_outstanding_amount_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'outstanding_amount')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_outstanding_amount_stability_threshold', 12.0)
    return _result('check_outstanding_amount_stability', adjusted, threshold, False, 'validates outstanding_amount stability',
                   {'field': 'outstanding_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_outstanding_amount_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'outstanding_amount')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_outstanding_amount_freshness_threshold', 14.333)
    return _result('check_outstanding_amount_freshness', adjusted, threshold, True, 'validates outstanding_amount freshness',
                   {'field': 'outstanding_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_outstanding_amount_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'outstanding_amount')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_outstanding_amount_coverage_threshold', 16.667)
    return _result('check_outstanding_amount_coverage', adjusted, threshold, True, 'validates outstanding_amount coverage',
                   {'field': 'outstanding_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_outstanding_amount_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'outstanding_amount')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_outstanding_amount_consistency_threshold', 19.0)
    return _result('check_outstanding_amount_consistency', adjusted, threshold, False, 'validates outstanding_amount consistency',
                   {'field': 'outstanding_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_outstanding_amount_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'outstanding_amount')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_outstanding_amount_risk_threshold', 21.333)
    return _result('check_outstanding_amount_risk', adjusted, threshold, True, 'validates outstanding_amount risk',
                   {'field': 'outstanding_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_outstanding_amount_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'outstanding_amount')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_outstanding_amount_confidence_threshold', 23.667)
    return _result('check_outstanding_amount_confidence', adjusted, threshold, True, 'validates outstanding_amount confidence',
                   {'field': 'outstanding_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_outstanding_amount_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'outstanding_amount')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_outstanding_amount_dependency_threshold', 26.0)
    return _result('check_outstanding_amount_dependency', adjusted, threshold, False, 'validates outstanding_amount dependency',
                   {'field': 'outstanding_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_outstanding_amount_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'outstanding_amount')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_outstanding_amount_readiness_threshold', 28.333)
    return _result('check_outstanding_amount_readiness', adjusted, threshold, True, 'validates outstanding_amount readiness',
                   {'field': 'outstanding_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_payment_coverage_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'payment_coverage')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_payment_coverage_presence_threshold', 30.667)
    return _result('check_payment_coverage_presence', adjusted, threshold, True, 'validates payment_coverage presence',
                   {'field': 'payment_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_payment_coverage_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'payment_coverage')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_payment_coverage_range_threshold', 8.667)
    return _result('check_payment_coverage_range', adjusted, threshold, False, 'validates payment_coverage range',
                   {'field': 'payment_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_payment_coverage_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'payment_coverage')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_payment_coverage_stability_threshold', 11.0)
    return _result('check_payment_coverage_stability', adjusted, threshold, True, 'validates payment_coverage stability',
                   {'field': 'payment_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_payment_coverage_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'payment_coverage')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_payment_coverage_freshness_threshold', 13.333)
    return _result('check_payment_coverage_freshness', adjusted, threshold, True, 'validates payment_coverage freshness',
                   {'field': 'payment_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_payment_coverage_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'payment_coverage')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_payment_coverage_coverage_threshold', 15.667)
    return _result('check_payment_coverage_coverage', adjusted, threshold, False, 'validates payment_coverage coverage',
                   {'field': 'payment_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_payment_coverage_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'payment_coverage')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_payment_coverage_consistency_threshold', 18.0)
    return _result('check_payment_coverage_consistency', adjusted, threshold, True, 'validates payment_coverage consistency',
                   {'field': 'payment_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_payment_coverage_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'payment_coverage')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_payment_coverage_risk_threshold', 20.333)
    return _result('check_payment_coverage_risk', adjusted, threshold, True, 'validates payment_coverage risk',
                   {'field': 'payment_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_payment_coverage_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'payment_coverage')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_payment_coverage_confidence_threshold', 22.667)
    return _result('check_payment_coverage_confidence', adjusted, threshold, False, 'validates payment_coverage confidence',
                   {'field': 'payment_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_payment_coverage_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'payment_coverage')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_payment_coverage_dependency_threshold', 25.0)
    return _result('check_payment_coverage_dependency', adjusted, threshold, True, 'validates payment_coverage dependency',
                   {'field': 'payment_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_payment_coverage_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'payment_coverage')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_payment_coverage_readiness_threshold', 27.333)
    return _result('check_payment_coverage_readiness', adjusted, threshold, True, 'validates payment_coverage readiness',
                   {'field': 'payment_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_waiver_amount_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'waiver_amount')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_waiver_amount_presence_threshold', 29.667)
    return _result('check_waiver_amount_presence', adjusted, threshold, False, 'validates waiver_amount presence',
                   {'field': 'waiver_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_waiver_amount_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'waiver_amount')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_waiver_amount_range_threshold', 32.0)
    return _result('check_waiver_amount_range', adjusted, threshold, True, 'validates waiver_amount range',
                   {'field': 'waiver_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_waiver_amount_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'waiver_amount')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_waiver_amount_stability_threshold', 10.0)
    return _result('check_waiver_amount_stability', adjusted, threshold, True, 'validates waiver_amount stability',
                   {'field': 'waiver_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_waiver_amount_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'waiver_amount')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_waiver_amount_freshness_threshold', 12.333)
    return _result('check_waiver_amount_freshness', adjusted, threshold, False, 'validates waiver_amount freshness',
                   {'field': 'waiver_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_waiver_amount_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'waiver_amount')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_waiver_amount_coverage_threshold', 14.667)
    return _result('check_waiver_amount_coverage', adjusted, threshold, True, 'validates waiver_amount coverage',
                   {'field': 'waiver_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_waiver_amount_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'waiver_amount')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_waiver_amount_consistency_threshold', 17.0)
    return _result('check_waiver_amount_consistency', adjusted, threshold, True, 'validates waiver_amount consistency',
                   {'field': 'waiver_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_waiver_amount_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'waiver_amount')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_waiver_amount_risk_threshold', 19.333)
    return _result('check_waiver_amount_risk', adjusted, threshold, False, 'validates waiver_amount risk',
                   {'field': 'waiver_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_waiver_amount_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'waiver_amount')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_waiver_amount_confidence_threshold', 21.667)
    return _result('check_waiver_amount_confidence', adjusted, threshold, True, 'validates waiver_amount confidence',
                   {'field': 'waiver_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_waiver_amount_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'waiver_amount')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_waiver_amount_dependency_threshold', 24.0)
    return _result('check_waiver_amount_dependency', adjusted, threshold, True, 'validates waiver_amount dependency',
                   {'field': 'waiver_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_waiver_amount_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'waiver_amount')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_waiver_amount_readiness_threshold', 26.333)
    return _result('check_waiver_amount_readiness', adjusted, threshold, False, 'validates waiver_amount readiness',
                   {'field': 'waiver_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_entitlement_units_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'entitlement_units')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_entitlement_units_presence_threshold', 28.667)
    return _result('check_entitlement_units_presence', adjusted, threshold, True, 'validates entitlement_units presence',
                   {'field': 'entitlement_units', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_entitlement_units_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'entitlement_units')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_entitlement_units_range_threshold', 31.0)
    return _result('check_entitlement_units_range', adjusted, threshold, True, 'validates entitlement_units range',
                   {'field': 'entitlement_units', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_entitlement_units_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'entitlement_units')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_entitlement_units_stability_threshold', 9.0)
    return _result('check_entitlement_units_stability', adjusted, threshold, False, 'validates entitlement_units stability',
                   {'field': 'entitlement_units', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_entitlement_units_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'entitlement_units')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_entitlement_units_freshness_threshold', 11.333)
    return _result('check_entitlement_units_freshness', adjusted, threshold, True, 'validates entitlement_units freshness',
                   {'field': 'entitlement_units', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_entitlement_units_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'entitlement_units')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_entitlement_units_coverage_threshold', 13.667)
    return _result('check_entitlement_units_coverage', adjusted, threshold, True, 'validates entitlement_units coverage',
                   {'field': 'entitlement_units', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_entitlement_units_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'entitlement_units')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_entitlement_units_consistency_threshold', 16.0)
    return _result('check_entitlement_units_consistency', adjusted, threshold, False, 'validates entitlement_units consistency',
                   {'field': 'entitlement_units', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_entitlement_units_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'entitlement_units')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_entitlement_units_risk_threshold', 18.333)
    return _result('check_entitlement_units_risk', adjusted, threshold, True, 'validates entitlement_units risk',
                   {'field': 'entitlement_units', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_entitlement_units_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'entitlement_units')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_entitlement_units_confidence_threshold', 20.667)
    return _result('check_entitlement_units_confidence', adjusted, threshold, True, 'validates entitlement_units confidence',
                   {'field': 'entitlement_units', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_entitlement_units_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'entitlement_units')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_entitlement_units_dependency_threshold', 23.0)
    return _result('check_entitlement_units_dependency', adjusted, threshold, False, 'validates entitlement_units dependency',
                   {'field': 'entitlement_units', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_entitlement_units_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'entitlement_units')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_entitlement_units_readiness_threshold', 25.333)
    return _result('check_entitlement_units_readiness', adjusted, threshold, True, 'validates entitlement_units readiness',
                   {'field': 'entitlement_units', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_amount_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_amount')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_assessment_amount_presence_threshold', 27.667)
    return _result('check_assessment_amount_presence', adjusted, threshold, True, 'validates assessment_amount presence',
                   {'field': 'assessment_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_amount_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_amount')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_assessment_amount_range_threshold', 30.0)
    return _result('check_assessment_amount_range', adjusted, threshold, False, 'validates assessment_amount range',
                   {'field': 'assessment_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_amount_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_amount')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_assessment_amount_stability_threshold', 8.0)
    return _result('check_assessment_amount_stability', adjusted, threshold, True, 'validates assessment_amount stability',
                   {'field': 'assessment_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_amount_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_amount')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_assessment_amount_freshness_threshold', 10.333)
    return _result('check_assessment_amount_freshness', adjusted, threshold, True, 'validates assessment_amount freshness',
                   {'field': 'assessment_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_amount_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_amount')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_assessment_amount_coverage_threshold', 12.667)
    return _result('check_assessment_amount_coverage', adjusted, threshold, False, 'validates assessment_amount coverage',
                   {'field': 'assessment_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_amount_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_amount')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_assessment_amount_consistency_threshold', 15.0)
    return _result('check_assessment_amount_consistency', adjusted, threshold, True, 'validates assessment_amount consistency',
                   {'field': 'assessment_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_amount_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_amount')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_assessment_amount_risk_threshold', 17.333)
    return _result('check_assessment_amount_risk', adjusted, threshold, True, 'validates assessment_amount risk',
                   {'field': 'assessment_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_amount_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_amount')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_assessment_amount_confidence_threshold', 19.667)
    return _result('check_assessment_amount_confidence', adjusted, threshold, False, 'validates assessment_amount confidence',
                   {'field': 'assessment_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_amount_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_amount')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_assessment_amount_dependency_threshold', 22.0)
    return _result('check_assessment_amount_dependency', adjusted, threshold, True, 'validates assessment_amount dependency',
                   {'field': 'assessment_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_assessment_amount_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'assessment_amount')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_assessment_amount_readiness_threshold', 24.333)
    return _result('check_assessment_amount_readiness', adjusted, threshold, True, 'validates assessment_amount readiness',
                   {'field': 'assessment_amount', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_fx_variance_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'fx_variance')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_fx_variance_presence_threshold', 26.667)
    return _result('check_fx_variance_presence', adjusted, threshold, False, 'validates fx_variance presence',
                   {'field': 'fx_variance', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_fx_variance_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'fx_variance')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_fx_variance_range_threshold', 29.0)
    return _result('check_fx_variance_range', adjusted, threshold, True, 'validates fx_variance range',
                   {'field': 'fx_variance', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_fx_variance_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'fx_variance')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_fx_variance_stability_threshold', 31.333)
    return _result('check_fx_variance_stability', adjusted, threshold, True, 'validates fx_variance stability',
                   {'field': 'fx_variance', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_fx_variance_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'fx_variance')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_fx_variance_freshness_threshold', 9.333)
    return _result('check_fx_variance_freshness', adjusted, threshold, False, 'validates fx_variance freshness',
                   {'field': 'fx_variance', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_fx_variance_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'fx_variance')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_fx_variance_coverage_threshold', 11.667)
    return _result('check_fx_variance_coverage', adjusted, threshold, True, 'validates fx_variance coverage',
                   {'field': 'fx_variance', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_fx_variance_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'fx_variance')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_fx_variance_consistency_threshold', 14.0)
    return _result('check_fx_variance_consistency', adjusted, threshold, True, 'validates fx_variance consistency',
                   {'field': 'fx_variance', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_fx_variance_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'fx_variance')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_fx_variance_risk_threshold', 16.333)
    return _result('check_fx_variance_risk', adjusted, threshold, False, 'validates fx_variance risk',
                   {'field': 'fx_variance', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_fx_variance_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'fx_variance')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_fx_variance_confidence_threshold', 18.667)
    return _result('check_fx_variance_confidence', adjusted, threshold, True, 'validates fx_variance confidence',
                   {'field': 'fx_variance', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_fx_variance_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'fx_variance')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_fx_variance_dependency_threshold', 21.0)
    return _result('check_fx_variance_dependency', adjusted, threshold, True, 'validates fx_variance dependency',
                   {'field': 'fx_variance', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_fx_variance_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'fx_variance')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_fx_variance_readiness_threshold', 23.333)
    return _result('check_fx_variance_readiness', adjusted, threshold, False, 'validates fx_variance readiness',
                   {'field': 'fx_variance', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delinquency_risk_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delinquency_risk')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_delinquency_risk_presence_threshold', 25.667)
    return _result('check_delinquency_risk_presence', adjusted, threshold, True, 'validates delinquency_risk presence',
                   {'field': 'delinquency_risk', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delinquency_risk_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delinquency_risk')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_delinquency_risk_range_threshold', 28.0)
    return _result('check_delinquency_risk_range', adjusted, threshold, True, 'validates delinquency_risk range',
                   {'field': 'delinquency_risk', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delinquency_risk_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delinquency_risk')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_delinquency_risk_stability_threshold', 30.333)
    return _result('check_delinquency_risk_stability', adjusted, threshold, False, 'validates delinquency_risk stability',
                   {'field': 'delinquency_risk', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delinquency_risk_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delinquency_risk')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_delinquency_risk_freshness_threshold', 8.333)
    return _result('check_delinquency_risk_freshness', adjusted, threshold, True, 'validates delinquency_risk freshness',
                   {'field': 'delinquency_risk', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delinquency_risk_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delinquency_risk')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_delinquency_risk_coverage_threshold', 10.667)
    return _result('check_delinquency_risk_coverage', adjusted, threshold, True, 'validates delinquency_risk coverage',
                   {'field': 'delinquency_risk', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delinquency_risk_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delinquency_risk')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_delinquency_risk_consistency_threshold', 13.0)
    return _result('check_delinquency_risk_consistency', adjusted, threshold, False, 'validates delinquency_risk consistency',
                   {'field': 'delinquency_risk', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delinquency_risk_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delinquency_risk')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_delinquency_risk_risk_threshold', 15.333)
    return _result('check_delinquency_risk_risk', adjusted, threshold, True, 'validates delinquency_risk risk',
                   {'field': 'delinquency_risk', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delinquency_risk_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delinquency_risk')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_delinquency_risk_confidence_threshold', 17.667)
    return _result('check_delinquency_risk_confidence', adjusted, threshold, True, 'validates delinquency_risk confidence',
                   {'field': 'delinquency_risk', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delinquency_risk_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delinquency_risk')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_delinquency_risk_dependency_threshold', 20.0)
    return _result('check_delinquency_risk_dependency', adjusted, threshold, False, 'validates delinquency_risk dependency',
                   {'field': 'delinquency_risk', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_delinquency_risk_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'delinquency_risk')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_delinquency_risk_readiness_threshold', 22.333)
    return _result('check_delinquency_risk_readiness', adjusted, threshold, True, 'validates delinquency_risk readiness',
                   {'field': 'delinquency_risk', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_service_cost_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'service_cost')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_service_cost_presence_threshold', 24.667)
    return _result('check_service_cost_presence', adjusted, threshold, True, 'validates service_cost presence',
                   {'field': 'service_cost', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_service_cost_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'service_cost')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_service_cost_range_threshold', 27.0)
    return _result('check_service_cost_range', adjusted, threshold, False, 'validates service_cost range',
                   {'field': 'service_cost', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_service_cost_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'service_cost')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_service_cost_stability_threshold', 29.333)
    return _result('check_service_cost_stability', adjusted, threshold, True, 'validates service_cost stability',
                   {'field': 'service_cost', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_service_cost_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'service_cost')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_service_cost_freshness_threshold', 31.667)
    return _result('check_service_cost_freshness', adjusted, threshold, True, 'validates service_cost freshness',
                   {'field': 'service_cost', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_service_cost_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'service_cost')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_service_cost_coverage_threshold', 9.667)
    return _result('check_service_cost_coverage', adjusted, threshold, False, 'validates service_cost coverage',
                   {'field': 'service_cost', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_service_cost_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'service_cost')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_service_cost_consistency_threshold', 12.0)
    return _result('check_service_cost_consistency', adjusted, threshold, True, 'validates service_cost consistency',
                   {'field': 'service_cost', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_service_cost_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'service_cost')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_service_cost_risk_threshold', 14.333)
    return _result('check_service_cost_risk', adjusted, threshold, True, 'validates service_cost risk',
                   {'field': 'service_cost', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_service_cost_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'service_cost')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_service_cost_confidence_threshold', 16.667)
    return _result('check_service_cost_confidence', adjusted, threshold, False, 'validates service_cost confidence',
                   {'field': 'service_cost', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_service_cost_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'service_cost')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_service_cost_dependency_threshold', 19.0)
    return _result('check_service_cost_dependency', adjusted, threshold, True, 'validates service_cost dependency',
                   {'field': 'service_cost', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_service_cost_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'service_cost')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_service_cost_readiness_threshold', 21.333)
    return _result('check_service_cost_readiness', adjusted, threshold, True, 'validates service_cost readiness',
                   {'field': 'service_cost', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_invoice_count_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'invoice_count')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_invoice_count_presence_threshold', 23.667)
    return _result('check_invoice_count_presence', adjusted, threshold, False, 'validates invoice_count presence',
                   {'field': 'invoice_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_invoice_count_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'invoice_count')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_invoice_count_range_threshold', 26.0)
    return _result('check_invoice_count_range', adjusted, threshold, True, 'validates invoice_count range',
                   {'field': 'invoice_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_invoice_count_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'invoice_count')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_invoice_count_stability_threshold', 28.333)
    return _result('check_invoice_count_stability', adjusted, threshold, True, 'validates invoice_count stability',
                   {'field': 'invoice_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_invoice_count_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'invoice_count')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_invoice_count_freshness_threshold', 30.667)
    return _result('check_invoice_count_freshness', adjusted, threshold, False, 'validates invoice_count freshness',
                   {'field': 'invoice_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_invoice_count_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'invoice_count')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_invoice_count_coverage_threshold', 8.667)
    return _result('check_invoice_count_coverage', adjusted, threshold, True, 'validates invoice_count coverage',
                   {'field': 'invoice_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_invoice_count_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'invoice_count')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_invoice_count_consistency_threshold', 11.0)
    return _result('check_invoice_count_consistency', adjusted, threshold, True, 'validates invoice_count consistency',
                   {'field': 'invoice_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_invoice_count_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'invoice_count')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_invoice_count_risk_threshold', 13.333)
    return _result('check_invoice_count_risk', adjusted, threshold, False, 'validates invoice_count risk',
                   {'field': 'invoice_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_invoice_count_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'invoice_count')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_invoice_count_confidence_threshold', 15.667)
    return _result('check_invoice_count_confidence', adjusted, threshold, True, 'validates invoice_count confidence',
                   {'field': 'invoice_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_invoice_count_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'invoice_count')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_invoice_count_dependency_threshold', 18.0)
    return _result('check_invoice_count_dependency', adjusted, threshold, True, 'validates invoice_count dependency',
                   {'field': 'invoice_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_invoice_count_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'invoice_count')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_invoice_count_readiness_threshold', 20.333)
    return _result('check_invoice_count_readiness', adjusted, threshold, False, 'validates invoice_count readiness',
                   {'field': 'invoice_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

RULES: tuple[RuleFunction, ...] = (
    check_member_category_presence,
    check_member_category_range,
    check_member_category_stability,
    check_member_category_freshness,
    check_member_category_coverage,
    check_member_category_consistency,
    check_member_category_risk,
    check_member_category_confidence,
    check_member_category_dependency,
    check_member_category_readiness,
    check_member_id_presence,
    check_member_id_range,
    check_member_id_stability,
    check_member_id_freshness,
    check_member_id_coverage,
    check_member_id_consistency,
    check_member_id_risk,
    check_member_id_confidence,
    check_member_id_dependency,
    check_member_id_readiness,
    check_assessment_basis_presence,
    check_assessment_basis_range,
    check_assessment_basis_stability,
    check_assessment_basis_freshness,
    check_assessment_basis_coverage,
    check_assessment_basis_consistency,
    check_assessment_basis_risk,
    check_assessment_basis_confidence,
    check_assessment_basis_dependency,
    check_assessment_basis_readiness,
    check_outstanding_amount_presence,
    check_outstanding_amount_range,
    check_outstanding_amount_stability,
    check_outstanding_amount_freshness,
    check_outstanding_amount_coverage,
    check_outstanding_amount_consistency,
    check_outstanding_amount_risk,
    check_outstanding_amount_confidence,
    check_outstanding_amount_dependency,
    check_outstanding_amount_readiness,
    check_payment_coverage_presence,
    check_payment_coverage_range,
    check_payment_coverage_stability,
    check_payment_coverage_freshness,
    check_payment_coverage_coverage,
    check_payment_coverage_consistency,
    check_payment_coverage_risk,
    check_payment_coverage_confidence,
    check_payment_coverage_dependency,
    check_payment_coverage_readiness,
    check_waiver_amount_presence,
    check_waiver_amount_range,
    check_waiver_amount_stability,
    check_waiver_amount_freshness,
    check_waiver_amount_coverage,
    check_waiver_amount_consistency,
    check_waiver_amount_risk,
    check_waiver_amount_confidence,
    check_waiver_amount_dependency,
    check_waiver_amount_readiness,
    check_entitlement_units_presence,
    check_entitlement_units_range,
    check_entitlement_units_stability,
    check_entitlement_units_freshness,
    check_entitlement_units_coverage,
    check_entitlement_units_consistency,
    check_entitlement_units_risk,
    check_entitlement_units_confidence,
    check_entitlement_units_dependency,
    check_entitlement_units_readiness,
    check_assessment_amount_presence,
    check_assessment_amount_range,
    check_assessment_amount_stability,
    check_assessment_amount_freshness,
    check_assessment_amount_coverage,
    check_assessment_amount_consistency,
    check_assessment_amount_risk,
    check_assessment_amount_confidence,
    check_assessment_amount_dependency,
    check_assessment_amount_readiness,
    check_fx_variance_presence,
    check_fx_variance_range,
    check_fx_variance_stability,
    check_fx_variance_freshness,
    check_fx_variance_coverage,
    check_fx_variance_consistency,
    check_fx_variance_risk,
    check_fx_variance_confidence,
    check_fx_variance_dependency,
    check_fx_variance_readiness,
    check_delinquency_risk_presence,
    check_delinquency_risk_range,
    check_delinquency_risk_stability,
    check_delinquency_risk_freshness,
    check_delinquency_risk_coverage,
    check_delinquency_risk_consistency,
    check_delinquency_risk_risk,
    check_delinquency_risk_confidence,
    check_delinquency_risk_dependency,
    check_delinquency_risk_readiness,
    check_service_cost_presence,
    check_service_cost_range,
    check_service_cost_stability,
    check_service_cost_freshness,
    check_service_cost_coverage,
    check_service_cost_consistency,
    check_service_cost_risk,
    check_service_cost_confidence,
    check_service_cost_dependency,
    check_service_cost_readiness,
    check_invoice_count_presence,
    check_invoice_count_range,
    check_invoice_count_stability,
    check_invoice_count_freshness,
    check_invoice_count_coverage,
    check_invoice_count_consistency,
    check_invoice_count_risk,
    check_invoice_count_confidence,
    check_invoice_count_dependency,
    check_invoice_count_readiness,
)

RULE_INDEX = {rule.__name__: rule for rule in RULES}

def evaluate(record: DomainRecord, context: Mapping[str, Any] | None = None) -> tuple[RuleResult, ...]:
    context = context or {}
    return tuple(rule(record, context) for rule in RULES)

def summarize(results: tuple[RuleResult, ...]) -> dict[str, Any]:
    if not results:
        return {'score': 0.0, 'passed': 0, 'failed': 0, 'critical': 0}
    return {'score': sum(item.score for item in results) / len(results),
            'passed': sum(item.passed for item in results),
            'failed': sum(not item.passed for item in results),
            'critical': sum(item.severity == 'critical' for item in results)}
