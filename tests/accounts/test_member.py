from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from member_settlement.accounts.member import ContractError, DomainRecord, RuleResult, bounded, stable_hash
from member_settlement.invoiced.rules import RULE_INDEX, evaluate, summarize
from member_settlement.payments.allocation_book import METRICS, compare, grouped_metrics, metric_vector, portfolio, record_score

FIELDS = ['member_category', 'member_id', 'assessment_basis', 'outstanding_amount', 'payment_coverage', 'waiver_amount', 'entitlement_units', 'assessment_amount', 'fx_variance', 'delinquency_risk', 'service_cost', 'invoice_count']

def make_record(seed: int = 1, state: str | None = None) -> DomainRecord:
    payload = {}
    for index, field in enumerate(FIELDS):
        selector = (seed + index) % 4
        if selector == 0:
            payload[field] = seed * 9.5 + index * 1.25
        elif selector == 1:
            payload[field] = f'{field}-{seed % 5}'
        elif selector == 2:
            payload[field] = (seed + index) / 10.0
        else:
            payload[field] = (seed + index) % 2 == 0
    return DomainRecord(f'member_account-{seed:03d}', payload, state or 'assessed')

class RuleGroup1Tests(unittest.TestCase):
    def test_evaluate_returns_complete_catalog(self):
        record = make_record()
        results = evaluate(record, {})
        self.assertEqual(len(results), len(RULE_INDEX))
        self.assertTrue(all(isinstance(item, RuleResult) for item in results))
        self.assertTrue(all(0.0 <= item.score <= 1.0 for item in results))

    def test_summary_is_conservative_and_counted(self):
        results = evaluate(make_record(2), {'risk_weight': 0.8})
        summary = summarize(results)
        self.assertEqual(summary['passed'] + summary['failed'], len(results))
        self.assertGreaterEqual(summary['critical'], 0)
        self.assertGreaterEqual(summary['score'], 0.0)
        self.assertLessEqual(summary['score'], 1.0)

    def test_check_member_category_presence_01_01(self):
        record = make_record(3)
        result = RULE_INDEX['check_member_category_presence'](record, {'check_member_category_presence_threshold': 1.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_category_presence')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_category_range_01_02(self):
        record = make_record(4)
        result = RULE_INDEX['check_member_category_range'](record, {'check_member_category_range_threshold': 2.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_category_range')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_category_stability_01_03(self):
        record = make_record(5)
        result = RULE_INDEX['check_member_category_stability'](record, {'check_member_category_stability_threshold': 3.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_category_stability')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_category_freshness_01_04(self):
        record = make_record(6)
        result = RULE_INDEX['check_member_category_freshness'](record, {'check_member_category_freshness_threshold': 4.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_category_freshness')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_category_coverage_01_05(self):
        record = make_record(7)
        result = RULE_INDEX['check_member_category_coverage'](record, {'check_member_category_coverage_threshold': 5.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_category_coverage')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_category_consistency_01_06(self):
        record = make_record(8)
        result = RULE_INDEX['check_member_category_consistency'](record, {'check_member_category_consistency_threshold': 6.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_category_consistency')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_category_risk_01_07(self):
        record = make_record(9)
        result = RULE_INDEX['check_member_category_risk'](record, {'check_member_category_risk_threshold': 7.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_category_risk')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_category_confidence_01_08(self):
        record = make_record(10)
        result = RULE_INDEX['check_member_category_confidence'](record, {'check_member_category_confidence_threshold': 8.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_category_confidence')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_category_dependency_01_09(self):
        record = make_record(11)
        result = RULE_INDEX['check_member_category_dependency'](record, {'check_member_category_dependency_threshold': 9.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_category_dependency')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_category_readiness_01_10(self):
        record = make_record(12)
        result = RULE_INDEX['check_member_category_readiness'](record, {'check_member_category_readiness_threshold': 1.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_category_readiness')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_id_presence_01_11(self):
        record = make_record(13)
        result = RULE_INDEX['check_member_id_presence'](record, {'check_member_id_presence_threshold': 2.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_id_presence')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_id_range_01_12(self):
        record = make_record(14)
        result = RULE_INDEX['check_member_id_range'](record, {'check_member_id_range_threshold': 3.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_id_range')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_id_stability_01_13(self):
        record = make_record(15)
        result = RULE_INDEX['check_member_id_stability'](record, {'check_member_id_stability_threshold': 4.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_id_stability')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_id_freshness_01_14(self):
        record = make_record(16)
        result = RULE_INDEX['check_member_id_freshness'](record, {'check_member_id_freshness_threshold': 5.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_id_freshness')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_id_coverage_01_15(self):
        record = make_record(17)
        result = RULE_INDEX['check_member_id_coverage'](record, {'check_member_id_coverage_threshold': 6.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_id_coverage')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_id_consistency_01_16(self):
        record = make_record(18)
        result = RULE_INDEX['check_member_id_consistency'](record, {'check_member_id_consistency_threshold': 7.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_id_consistency')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_id_risk_01_17(self):
        record = make_record(19)
        result = RULE_INDEX['check_member_id_risk'](record, {'check_member_id_risk_threshold': 8.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_id_risk')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_id_confidence_01_18(self):
        record = make_record(20)
        result = RULE_INDEX['check_member_id_confidence'](record, {'check_member_id_confidence_threshold': 9.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_id_confidence')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_id_dependency_01_19(self):
        record = make_record(21)
        result = RULE_INDEX['check_member_id_dependency'](record, {'check_member_id_dependency_threshold': 1.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_id_dependency')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_member_id_readiness_01_20(self):
        record = make_record(22)
        result = RULE_INDEX['check_member_id_readiness'](record, {'check_member_id_readiness_threshold': 2.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_member_id_readiness')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_assessment_basis_presence_01_21(self):
        record = make_record(23)
        result = RULE_INDEX['check_assessment_basis_presence'](record, {'check_assessment_basis_presence_threshold': 3.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_assessment_basis_presence')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_assessment_basis_range_01_22(self):
        record = make_record(24)
        result = RULE_INDEX['check_assessment_basis_range'](record, {'check_assessment_basis_range_threshold': 4.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_assessment_basis_range')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_assessment_basis_stability_01_23(self):
        record = make_record(25)
        result = RULE_INDEX['check_assessment_basis_stability'](record, {'check_assessment_basis_stability_threshold': 5.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_assessment_basis_stability')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_assessment_basis_freshness_01_24(self):
        record = make_record(26)
        result = RULE_INDEX['check_assessment_basis_freshness'](record, {'check_assessment_basis_freshness_threshold': 6.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_assessment_basis_freshness')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_assessment_basis_coverage_01_25(self):
        record = make_record(27)
        result = RULE_INDEX['check_assessment_basis_coverage'](record, {'check_assessment_basis_coverage_threshold': 7.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_assessment_basis_coverage')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_assessment_basis_consistency_01_26(self):
        record = make_record(28)
        result = RULE_INDEX['check_assessment_basis_consistency'](record, {'check_assessment_basis_consistency_threshold': 8.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_assessment_basis_consistency')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_assessment_basis_risk_01_27(self):
        record = make_record(29)
        result = RULE_INDEX['check_assessment_basis_risk'](record, {'check_assessment_basis_risk_threshold': 9.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_assessment_basis_risk')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_assessment_basis_confidence_01_28(self):
        record = make_record(30)
        result = RULE_INDEX['check_assessment_basis_confidence'](record, {'check_assessment_basis_confidence_threshold': 1.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_assessment_basis_confidence')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_assessment_basis_dependency_01_29(self):
        record = make_record(31)
        result = RULE_INDEX['check_assessment_basis_dependency'](record, {'check_assessment_basis_dependency_threshold': 2.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_assessment_basis_dependency')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

    def test_check_assessment_basis_readiness_01_30(self):
        record = make_record(32)
        result = RULE_INDEX['check_assessment_basis_readiness'](record, {'check_assessment_basis_readiness_threshold': 3.0})
        self.assertIsInstance(result, RuleResult)
        self.assertEqual(result.code, 'check_assessment_basis_readiness')
        self.assertIn(result.severity, {'info', 'warning', 'error', 'critical'})
        self.assertTrue(math.isfinite(result.score))
        self.assertIn('field', result.evidence)
        self.assertIn('threshold', result.evidence)

class MetricGroup1Tests(unittest.TestCase):
    def test_metric_vector_is_deterministic(self):
        record = make_record(11)
        first = metric_vector(record, {})
        second = metric_vector(record, {})
        self.assertEqual(first, second)
        self.assertEqual(set(first), set(METRICS))
        self.assertTrue(all(0.0 <= value <= 1.0 for value in first.values()))

    def test_grouped_metrics_match_business_catalog(self):
        grouped = grouped_metrics(make_record(4), {})
        self.assertEqual(set(grouped), {'policy_exposure', 'commercial_resilience', 'capacity_fit', 'readiness_index', 'concentration_risk', 'evidence_diversity', 'portfolio_value', 'dependency_fragility'})
        self.assertTrue(all(math.isfinite(value) for value in grouped.values()))

    def test_portfolio_orders_by_descending_score(self):
        result = portfolio([make_record(2), make_record(3), make_record(4)])
        scores = [row['score'] for row in result['rows']]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(result['count'], 3)
        self.assertGreaterEqual(result['maximum'], result['minimum'])

    def test_compare_has_all_metric_deltas(self):
        result = compare(make_record(5), make_record(6))
        self.assertEqual(set(result['delta']), {'policy_exposure', 'commercial_resilience', 'capacity_fit', 'readiness_index', 'concentration_risk', 'evidence_diversity', 'portfolio_value', 'dependency_fragility'})
        self.assertIn(result['winner'], {make_record(5).record_id, make_record(6).record_id})

    def test_score_fingerprint_changes_with_payload(self):
        left = record_score(make_record(7))
        right = record_score(make_record(8))
        self.assertNotEqual(left['fingerprint'], right['fingerprint'])
        self.assertNotEqual(stable_hash(left['metrics']), stable_hash(right['metrics']))

if __name__ == '__main__':
    unittest.main()
