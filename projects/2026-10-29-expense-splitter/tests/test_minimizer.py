"""Unit tests for cash flow minimization algorithm."""

import unittest
from decimal import Decimal
from expense_splitter.calculator import ExpenseGroup
from expense_splitter.minimizer import minimize_cash_flow
from expense_splitter.models import Expense, SplitType


class TestMinimizer(unittest.TestCase):

    def test_two_person_settlement(self):
        group = ExpenseGroup()
        group.add_expense(
            Expense(
                description="Movie",
                payer="Alice",
                amount=Decimal("30.00"),
                split_type=SplitType.EQUAL,
            )
        )
        group.add_participant("Bob")

        balances = group.get_balances()
        settlements = minimize_cash_flow(balances)

        self.assertEqual(len(settlements), 1)
        self.assertEqual(settlements[0].debtor, "Bob")
        self.assertEqual(settlements[0].creditor, "Alice")
        self.assertEqual(settlements[0].amount, Decimal("15.00"))

    def test_three_person_circular_debt_reduction(self):
        # Alice pays $30 for Bob
        # Bob pays $30 for Charlie
        # Charlie pays $30 for Alice
        # Everyone paid $30 and consumed $30 -> Net balance for all should be $0!
        group = ExpenseGroup()
        group.add_expense(
            Expense(description="A for B", payer="Alice", amount=Decimal("30.00"), splits=[])
        )
        # Use exact group logic
        g = ExpenseGroup()
        g.add_participant("Alice")
        g.add_participant("Bob")
        g.add_participant("Charlie")

        from expense_splitter.models import SplitShare

        g.add_expense(
            Expense(
                description="1",
                payer="Alice",
                amount=Decimal("30.00"),
                split_type=SplitType.EXACT,
                splits=[SplitShare("Bob", Decimal("30.00"))],
            )
        )
        g.add_expense(
            Expense(
                description="2",
                payer="Bob",
                amount=Decimal("30.00"),
                split_type=SplitType.EXACT,
                splits=[SplitShare("Charlie", Decimal("30.00"))],
            )
        )
        g.add_expense(
            Expense(
                description="3",
                payer="Charlie",
                amount=Decimal("30.00"),
                split_type=SplitType.EXACT,
                splits=[SplitShare("Alice", Decimal("30.00"))],
            )
        )

        balances = g.get_balances()
        self.assertEqual(balances["Alice"].net_balance, Decimal("0.00"))
        self.assertEqual(balances["Bob"].net_balance, Decimal("0.00"))
        self.assertEqual(balances["Charlie"].net_balance, Decimal("0.00"))

        settlements = minimize_cash_flow(balances)
        self.assertEqual(len(settlements), 0)

    def test_complex_group_settlement_invariants(self):
        # Test 4-person trip
        from expense_splitter.cli import build_sample_trip

        group = build_sample_trip()
        balances = group.get_balances()
        settlements = minimize_cash_flow(balances)

        # Invariant 1: Total transactions <= N - 1
        self.assertLessEqual(len(settlements), len(group.participants) - 1)

        # Invariant 2: Applying settlements zeroes out all net balances
        virtual_balances = {p: b.net_balance for p, b in balances.items()}
        for s in settlements:
            virtual_balances[s.debtor] += s.amount
            virtual_balances[s.creditor] -= s.amount

        for p, final_bal in virtual_balances.items():
            self.assertEqual(final_bal, Decimal("0.00"), f"Participant {p} not fully settled!")


if __name__ == "__main__":
    unittest.main()
