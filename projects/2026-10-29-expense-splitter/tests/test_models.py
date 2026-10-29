"""Unit tests for models and split calculations."""

import unittest
from decimal import Decimal
from expense_splitter.models import Participant, Expense, SplitType, SplitShare


class TestModels(unittest.TestCase):

    def test_participant_validation(self):
        p = Participant("  Alice  ")
        self.assertEqual(p.name, "Alice")

        with self.assertRaises(ValueError):
            Participant("")
        with self.assertRaises(ValueError):
            Participant("   ")

    def test_expense_amount_validation(self):
        e = Expense(description="Coffee", payer="Bob", amount=Decimal("4.50"))
        self.assertEqual(e.amount, Decimal("4.50"))

        # Zero and negative amounts
        with self.assertRaises(ValueError):
            Expense(description="Free", payer="Bob", amount=Decimal("0.00"))
        with self.assertRaises(ValueError):
            Expense(description="Refund", payer="Bob", amount=Decimal("-10.00"))

    def test_equal_split_no_lost_pennies(self):
        # $100.00 split among 3 people: $33.34, $33.33, $33.33
        participants = ["Alice", "Bob", "Charlie"]
        exp = Expense(
            description="Dinner",
            payer="Alice",
            amount=Decimal("100.00"),
            split_type=SplitType.EQUAL,
        )
        shares = exp.compute_individual_shares(participants)
        self.assertEqual(sum(shares.values()), Decimal("100.00"))
        self.assertEqual(shares["Alice"], Decimal("33.34"))
        self.assertEqual(shares["Bob"], Decimal("33.33"))
        self.assertEqual(shares["Charlie"], Decimal("33.33"))

    def test_equal_split_subset(self):
        participants = ["Alice", "Bob", "Charlie", "Diana"]
        exp = Expense(
            description="Drinks",
            payer="Bob",
            amount=Decimal("30.00"),
            split_type=SplitType.EQUAL,
            splits=[SplitShare("Alice"), SplitShare("Charlie")],
        )
        shares = exp.compute_individual_shares(participants)
        self.assertEqual(shares, {"Alice": Decimal("15.00"), "Charlie": Decimal("15.00")})
        self.assertEqual(sum(shares.values()), Decimal("30.00"))

    def test_exact_split(self):
        participants = ["Alice", "Bob"]
        exp = Expense(
            description="Taxi",
            payer="Alice",
            amount=Decimal("25.50"),
            split_type=SplitType.EXACT,
            splits=[
                SplitShare("Alice", Decimal("15.50")),
                SplitShare("Bob", Decimal("10.00")),
            ],
        )
        shares = exp.compute_individual_shares(participants)
        self.assertEqual(shares["Alice"], Decimal("15.50"))
        self.assertEqual(shares["Bob"], Decimal("10.00"))

        # Mismatch amount
        bad_exp = Expense(
            description="Taxi Mismatch",
            payer="Alice",
            amount=Decimal("25.50"),
            split_type=SplitType.EXACT,
            splits=[
                SplitShare("Alice", Decimal("15.00")),
                SplitShare("Bob", Decimal("10.00")),
            ],
        )
        with self.assertRaises(ValueError):
            bad_exp.compute_individual_shares(participants)

    def test_percentage_split(self):
        participants = ["Alice", "Bob", "Charlie"]
        exp = Expense(
            description="Project Costs",
            payer="Alice",
            amount=Decimal("100.00"),
            split_type=SplitType.PERCENTAGE,
            splits=[
                SplitShare("Alice", Decimal("50.0")),
                SplitShare("Bob", Decimal("30.0")),
                SplitShare("Charlie", Decimal("20.0")),
            ],
        )
        shares = exp.compute_individual_shares(participants)
        self.assertEqual(shares["Alice"], Decimal("50.00"))
        self.assertEqual(shares["Bob"], Decimal("30.00"))
        self.assertEqual(shares["Charlie"], Decimal("20.00"))
        self.assertEqual(sum(shares.values()), Decimal("100.00"))

        # Bad percentage sum
        bad_exp = Expense(
            description="Bad Pct",
            payer="Alice",
            amount=Decimal("100.00"),
            split_type=SplitType.PERCENTAGE,
            splits=[
                SplitShare("Alice", Decimal("50.0")),
                SplitShare("Bob", Decimal("40.0")),
            ],
        )
        with self.assertRaises(ValueError):
            bad_exp.compute_individual_shares(participants)

    def test_shares_weighted_split(self):
        participants = ["Alice", "Bob"]
        # Alice consumed 2 shares, Bob consumed 1 share of $99.00
        exp = Expense(
            description="Catering",
            payer="Alice",
            amount=Decimal("99.00"),
            split_type=SplitType.SHARES,
            splits=[
                SplitShare("Alice", Decimal("2")),
                SplitShare("Bob", Decimal("1")),
            ],
        )
        shares = exp.compute_individual_shares(participants)
        self.assertEqual(shares["Alice"], Decimal("66.00"))
        self.assertEqual(shares["Bob"], Decimal("33.00"))
        self.assertEqual(sum(shares.values()), Decimal("99.00"))


if __name__ == "__main__":
    unittest.main()
