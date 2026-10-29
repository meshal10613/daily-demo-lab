"""Unit tests for ledger calculator and balance calculations."""

import unittest
from decimal import Decimal
from expense_splitter.calculator import ExpenseGroup
from expense_splitter.models import Expense, SplitType, SplitShare


class TestCalculator(unittest.TestCase):

    def test_group_balances_and_totals(self):
        group = ExpenseGroup(name="Trip")
        group.add_participant("Alice")
        group.add_participant("Bob")

        # Alice pays $60 for both
        group.add_expense(
            Expense(
                description="Lunch",
                payer="Alice",
                amount=Decimal("60.00"),
                category="Food",
                split_type=SplitType.EQUAL,
            )
        )

        # Bob pays $40 for both
        group.add_expense(
            Expense(
                description="Dessert",
                payer="Bob",
                amount=Decimal("40.00"),
                category="Food",
                split_type=SplitType.EQUAL,
            )
        )

        self.assertEqual(group.get_total_spending(), Decimal("100.00"))
        self.assertEqual(group.get_category_spending(), {"Food": Decimal("100.00")})

        balances = group.get_balances()

        # Alice: paid 60, owed 30 + 20 = 50 -> net +10
        self.assertEqual(balances["Alice"].total_paid, Decimal("60.00"))
        self.assertEqual(balances["Alice"].total_owed, Decimal("50.00"))
        self.assertEqual(balances["Alice"].net_balance, Decimal("10.00"))

        # Bob: paid 40, owed 30 + 20 = 50 -> net -10
        self.assertEqual(balances["Bob"].total_paid, Decimal("40.00"))
        self.assertEqual(balances["Bob"].total_owed, Decimal("50.00"))
        self.assertEqual(balances["Bob"].net_balance, Decimal("-10.00"))

    def test_auto_participant_registration(self):
        group = ExpenseGroup()
        # Adding expense with unregistered payer and splits
        group.add_expense(
            Expense(
                description="Tickets",
                payer="Zara",
                amount=Decimal("150.00"),
                split_type=SplitType.EQUAL,
                splits=[SplitShare("Zara"), SplitShare("Liam")],
            )
        )
        self.assertIn("Zara", group.participants)
        self.assertIn("Liam", group.participants)
        self.assertEqual(group.get_total_spending(), Decimal("150.00"))


if __name__ == "__main__":
    unittest.main()
