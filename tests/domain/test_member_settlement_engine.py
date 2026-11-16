from __future__ import annotations

import unittest
from member_settlement.accounts.member import DomainRecord
from member_settlement.payments.payment_allocation import evaluate_choice, member_profile, optimize, shock


class SelectionTests(unittest.TestCase):
    def record(self, key, country="th", revenue=100):
        return DomainRecord(key, {"member_category": "robot", "member_id": country, "assessment_basis": .8,
            "outstanding_amount": .2, "payment_coverage": .8, "waiver_amount": 10, "entitlement_units": 4,
            "assessment_amount": revenue, "fx_variance": .2, "delinquency_risk": .2, "service_cost": 5, "invoice_count": 2})

    def test_capacity_and_concentration_constraints(self):
        rows = [self.record("a", "th", 120), self.record("b", "vn", 100), self.record("c", "th", 80)]
        choice = optimize(rows, capacity_limit=8, concentration_limit=.6)
        self.assertTrue(choice.feasible)
        self.assertLessEqual(choice.capacity, 8)
        self.assertFalse(evaluate_choice(rows, 5, .5).feasible)

    def test_shock_reduces_value(self):
        result = shock(self.record("a"), .3, .3)
        self.assertLess(result["shocked_value"], result["base_value"])
        self.assertGreater(member_profile(self.record("a"))["readiness"], .5)
