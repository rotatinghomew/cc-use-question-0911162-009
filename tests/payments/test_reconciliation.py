from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from member_settlement.ledger.settlement_store import Repository
from member_settlement.payments.reconciliation import ReconciliationBook, ReconciliationError


def book_with_bill(settlement: str = "USD") -> ReconciliationBook:
    book = ReconciliationBook(settlement)
    book.record_rate("EUR", settlement, "1.10", "2026-01-15")
    book.record_charge("charge-1", "member-1", "2026Q1", settlement, "1000.00",
                       "2026-01-20", "2026-01-15", "10")
    book.record_rate("EUR", settlement, "1.25", "2026-02-15")
    return book


class IdentityTests(unittest.TestCase):
    def test_receipts_fx_waivers_and_outstanding_explain_the_bill(self):
        book = book_with_bill()
        book.post_receipt("payment-1", "member-1", "EUR", "400.00", "USD", "2026-02-16")
        book.allocate("payment-1", "charge-1", "500.00")
        book.record_waiver("waiver-1", "charge-1", "USD", "100.00", "2026-02-20", "hardship")
        row = book.reconcile_charge("charge-1")

        self.assertTrue(row.identity_holds)
        self.assertEqual(row.charged, Decimal("1000.00"))
        self.assertEqual(row.receipts_cash_applied, Decimal("500.00"))
        # 400 EUR @ 1.25 costs 500 USD; restated at the bill's 2026-01-15 rate of 1.10 it is 440 USD.
        self.assertEqual(row.receipts_settled, Decimal("440.00"))
        self.assertEqual(row.fx_variance, Decimal("60.00"))
        self.assertEqual(row.waiver_amount, Decimal("100.00"))
        self.assertEqual(row.outstanding_amount, Decimal("400.00"))
        self.assertEqual(row.explained_amount, row.charged)

    def test_outstanding_excludes_fx_and_waivers(self):
        book = book_with_bill()
        book.post_receipt("payment-1", "member-1", "EUR", "400.00", "USD", "2026-02-16")
        book.allocate("payment-1", "charge-1", "500.00")
        book.record_waiver("waiver-1", "charge-1", "USD", "100.00", "2026-02-20")
        row = book.reconcile_charge("charge-1")
        self.assertNotEqual(row.outstanding_amount, row.charged - row.receipts_cash_applied)
        self.assertEqual(row.outstanding_amount, Decimal("400.00"))

    def test_same_currency_receipt_has_no_fx_variance(self):
        book = ReconciliationBook("USD")
        book.record_charge("charge-1", "member-1", "2026Q1", "USD", "100.00", "2026-01-05", "2026-01-05", "4")
        book.post_receipt("payment-1", "member-1", "USD", "60.00", "USD", "2026-01-06")
        book.allocate("payment-1", "charge-1", "60.00")
        row = book.reconcile_charge("charge-1")
        self.assertEqual(row.fx_variance, Decimal("0.00"))
        self.assertEqual(row.outstanding_amount, Decimal("40.00"))
        self.assertTrue(row.identity_holds)

    def test_overpayment_is_reported_as_credit_not_negative_arrears(self):
        book = ReconciliationBook("USD")
        book.record_charge("charge-1", "member-1", "2026Q1", "USD", "100.00", "2026-01-05", "2026-01-05", "4")
        book.post_receipt("payment-1", "member-1", "USD", "100.00", "USD", "2026-01-06")
        book.post_receipt("payment-2", "member-1", "USD", "25.00", "USD", "2026-01-07")
        book.allocate("payment-1", "charge-1", "100.00")
        with self.assertRaisesRegex(ReconciliationError, "already fully funded"):
            book.allocate("payment-2", "charge-1", "25.00")
        self.assertEqual(len(book.unapplied_receipts()), 1)
        self.assertEqual(book.unapplied_receipts()[0]["unapplied_settlement"], "25.00")

    def test_release_is_proportional_to_funded_balance(self):
        book = book_with_bill()
        book.post_receipt("payment-1", "member-1", "EUR", "400.00", "USD", "2026-02-16")
        book.allocate("payment-1", "charge-1", "500.00")
        book.record_waiver("waiver-1", "charge-1", "USD", "100.00", "2026-02-20")
        row = book.reconcile_charge("charge-1")
        self.assertEqual(row.coverage_ratio, Decimal("0.6000"))
        self.assertEqual(row.releasable_units, Decimal("6.0000"))
        self.assertLessEqual(row.releasable_units, row.entitlement_units)


class TraceabilityTests(unittest.TestCase):
    def test_receipt_keeps_original_currency_settlement_currency_rate_and_date(self):
        book = book_with_bill()
        receipt = book.post_receipt("payment-1", "member-1", "EUR", "400.00", "USD", "2026-02-16",
                                    rate_date="2026-02-15")
        self.assertEqual(receipt.original_currency, "EUR")
        self.assertEqual(receipt.original_amount, Decimal("400.00"))
        self.assertEqual(receipt.settlement_currency, "USD")
        self.assertEqual(receipt.settlement_value, Decimal("500.00"))
        self.assertEqual(receipt.applied_rate, Decimal("1.25000000"))
        self.assertEqual(receipt.rate_date.isoformat(), "2026-02-15")
        self.assertIn("rate_date", receipt.as_dict())
        self.assertEqual(receipt.as_dict()["applied_rate"], "1.25000000")

    def test_missing_rate_for_the_payment_date_is_rejected(self):
        book = ReconciliationBook("USD")
        with self.assertRaisesRegex(ReconciliationError, "no EUR/USD FX rate"):
            book.post_receipt("payment-1", "member-1", "EUR", "10.00", "USD", "2026-02-16")

    def test_manual_rate_override_is_honoured_and_traceable(self):
        book = book_with_bill()
        receipt = book.post_receipt("payment-1", "member-1", "EUR", "100.00", "USD", "2026-02-16",
                                    rate_date="2026-01-15")
        self.assertEqual(receipt.applied_rate, Decimal("1.10000000"))
        self.assertEqual(receipt.settlement_value, Decimal("110.00"))


class ClosedPeriodTests(unittest.TestCase):
    def setUp(self):
        self.book = book_with_bill()
        self.book.post_receipt("payment-1", "member-1", "EUR", "400.00", "USD", "2026-02-16")
        self.book.allocate("payment-1", "charge-1", "500.00")
        self.book.close_period("2026Q1", "2026-03-31")

    def test_close_freezes_a_reproducible_snapshot(self):
        snapshot = self.book.period_snapshot("2026Q1")
        self.assertEqual(snapshot["snapshot_hash"], self.book.period_report("2026Q1")["snapshot"]["snapshot_hash"])
        self.assertTrue(self.book.period_report("2026Q1")["immutable"])
        self.assertTrue(any(item["rate_date"] <= "2026-03-31" for item in snapshot["rates"]))

    def test_historic_rate_cannot_be_rewritten(self):
        with self.assertRaisesRegex(ReconciliationError, "closed period 2026Q1 history is immutable"):
            self.book.record_rate("EUR", "USD", "1.50", "2026-02-20")

    def test_existing_historic_rate_is_pinned_even_before_close(self):
        open_book = book_with_bill()
        with self.assertRaisesRegex(ReconciliationError, "cannot rewrite historical FX rate"):
            open_book.record_rate("EUR", "USD", "1.30", "2026-01-15")

    def test_closed_bill_cannot_be_rewritten(self):
        with self.assertRaisesRegex(ReconciliationError, "bills are immutable"):
            self.book.amend_charge("charge-1", amount="1200.00")

    def test_late_receipt_must_use_a_correction_period(self):
        with self.assertRaisesRegex(ReconciliationError, "falls in closed period 2026Q1"):
            self.book.post_receipt("payment-2", "member-1", "EUR", "100.00", "USD", "2026-02-25")
        late = self.book.post_receipt("payment-2", "member-1", "EUR", "100.00", "USD", "2026-02-25",
                                      correction_period_id="2026Q1-CORR-1", reason="late advice")
        self.assertEqual(late.original_period_id, "2026Q1")
        self.assertEqual(late.correction_period_id, "2026Q1-CORR-1")

    def test_late_allocation_must_use_a_correction_period(self):
        self.book.post_receipt("payment-2", "member-1", "USD", "100.00", "USD", "2026-02-25",
                               correction_period_id="2026Q1-CORR-1")
        with self.assertRaisesRegex(ReconciliationError, "must allocate through a correction period"):
            self.book.allocate("payment-2", "charge-1", "100.00")
        allocation = self.book.allocate("payment-2", "charge-1", "100.00",
                                        correction_period_id="2026Q1-CORR-1")
        self.assertEqual(allocation.correction_period_id, "2026Q1-CORR-1")
        kinds = [item["kind"] for item in self.book.corrections]
        self.assertIn("late_receipt", kinds)
        self.assertIn("late_allocation", kinds)

    def test_late_waiver_must_use_a_correction_period(self):
        with self.assertRaisesRegex(ReconciliationError, "record the waiver through a correction period"):
            self.book.record_waiver("waiver-1", "charge-1", "USD", "10.00", "2026-02-25")


class DuplicateAllocationTests(unittest.TestCase):
    def test_reposting_the_same_receipt_is_idempotent(self):
        book = book_with_bill()
        first = book.post_receipt("payment-1", "member-1", "EUR", "400.00", "USD", "2026-02-16")
        second = book.post_receipt("payment-1", "member-1", "EUR", "400.00", "USD", "2026-02-16")
        self.assertEqual(first.as_dict(), second.as_dict())
        self.assertEqual(len(book.receipts), 1)

    def test_reposting_the_same_payment_with_new_terms_is_rejected(self):
        book = book_with_bill()
        book.post_receipt("payment-1", "member-1", "EUR", "400.00", "USD", "2026-02-16")
        with self.assertRaisesRegex(ReconciliationError, "already exists with different terms"):
            book.post_receipt("payment-1", "member-1", "EUR", "450.00", "USD", "2026-02-16")

    def test_replaying_an_allocation_does_not_duplicate_it(self):
        book = book_with_bill()
        book.post_receipt("payment-1", "member-1", "EUR", "400.00", "USD", "2026-02-16")
        first = book.allocate("payment-1", "charge-1", "500.00")
        second = book.allocate("payment-1", "charge-1", "500.00")
        self.assertEqual(first.allocation_id, second.allocation_id)
        self.assertEqual(len(book.allocations), 1)
        self.assertEqual(book.reconcile_charge("charge-1").receipts_cash_applied, Decimal("500.00"))

    def test_reversing_a_receipt_requires_reversing_allocations_first(self):
        book = book_with_bill()
        book.post_receipt("payment-1", "member-1", "EUR", "400.00", "USD", "2026-02-16")
        allocation = book.allocate("payment-1", "charge-1", "500.00")
        with self.assertRaisesRegex(ReconciliationError, "reverse the payment allocations"):
            book.reverse_receipt("payment-1")
        book.reverse_allocation(allocation.allocation_id)
        book.reverse_receipt("payment-1")
        self.assertEqual(book.reconcile_charge("charge-1").receipts_cash_applied, Decimal("0.00"))
        self.assertEqual(book.reconcile_charge("charge-1").outstanding_amount, Decimal("1000.00"))


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repository = Repository(Path(self.temp.name) / "book.sqlite3")

    def test_reconciliation_survives_reload(self):
        book = book_with_bill()
        book.post_receipt("payment-1", "member-1", "EUR", "400.00", "USD", "2026-02-16")
        book.allocate("payment-1", "charge-1", "500.00")
        book.record_waiver("waiver-1", "charge-1", "USD", "100.00", "2026-02-20")
        book.close_period("2026Q1", "2026-03-31")
        self.repository.persist_reconciliation(book)

        reloaded = self.repository.load_reconciliation_book("USD")
        self.assertEqual(reloaded.reconcile(), book.reconcile())
        self.assertIn("2026Q1", reloaded.closed_periods)

    def test_repersisting_an_unchanged_book_does_not_grow_history(self):
        book = book_with_bill()
        self.repository.persist_reconciliation(book)
        before = self.repository.snapshot()["counts"]
        self.repository.persist_reconciliation(self.repository.load_reconciliation_book("USD"))
        self.assertEqual(before, self.repository.snapshot()["counts"])

    def test_persisted_closed_rate_is_immutable(self):
        book = book_with_bill()
        book.close_period("2026Q1", "2026-03-31")
        self.repository.persist_reconciliation(book)

        conflict = ReconciliationBook("USD")
        conflict.record_rate("EUR", "USD", "1.99", "2026-02-01")
        with self.assertRaisesRegex(Exception, "immutable"):
            self.repository.persist_reconciliation(conflict)


if __name__ == "__main__":
    unittest.main()
