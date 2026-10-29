"""Calculation engine for expense groups, spending totals, and net balances."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional
from .models import Participant, Expense, to_cents


@dataclass
class BalanceSummary:
    """Summary of financial participation for an individual."""
    participant: str
    total_paid: Decimal
    total_owed: Decimal

    @property
    def net_balance(self) -> Decimal:
        """Positive means owed money by others; negative means owes money to others."""
        return self.total_paid - self.total_owed


class ExpenseGroup:
    """Manages participants, expenses, and ledger calculations for a group."""

    def __init__(self, name: str = "Group Ledger"):
        self.name = name.strip() or "Group Ledger"
        self._participants: Dict[str, Participant] = {}
        self._expenses: List[Expense] = []

    @property
    def participants(self) -> List[str]:
        return sorted(self._participants.keys())

    @property
    def expenses(self) -> List[Expense]:
        return list(self._expenses)

    def add_participant(self, name: str) -> Participant:
        p = Participant(name)
        if p.name in self._participants:
            return self._participants[p.name]
        self._participants[p.name] = p
        return p

    def add_expense(self, expense: Expense) -> None:
        # Auto-register payer if not present
        if expense.payer not in self._participants:
            self.add_participant(expense.payer)

        # Validate that all targets are registered or register them
        if expense.splits:
            for s in expense.splits:
                if s.participant not in self._participants:
                    self.add_participant(s.participant)

        self._expenses.append(expense)

    def get_total_spending(self) -> Decimal:
        """Returns the total amount spent across all recorded expenses."""
        return sum((e.amount for e in self._expenses), Decimal("0.00"))

    def get_category_spending(self) -> Dict[str, Decimal]:
        """Returns total spending broken down by category."""
        breakdown: Dict[str, Decimal] = {}
        for exp in self._expenses:
            cat = exp.category
            breakdown[cat] = breakdown.get(cat, Decimal("0.00")) + exp.amount
        return dict(sorted(breakdown.items(), key=lambda x: x[1], reverse=True))

    def get_balances(self) -> Dict[str, BalanceSummary]:
        """
        Computes the paid, owed, and net balance for every participant.
        Guarantees that sum(net_balances) == Decimal('0.00').
        """
        all_parts = self.participants
        paid_map: Dict[str, Decimal] = {p: Decimal("0.00") for p in all_parts}
        owed_map: Dict[str, Decimal] = {p: Decimal("0.00") for p in all_parts}

        for exp in self._expenses:
            # Credit the payer
            paid_map[exp.payer] = paid_map.get(exp.payer, Decimal("0.00")) + exp.amount

            # Debit each beneficiary's owed amount
            shares = exp.compute_individual_shares(all_parts)
            for person, share in shares.items():
                owed_map[person] = owed_map.get(person, Decimal("0.00")) + share

        summaries: Dict[str, BalanceSummary] = {}
        for p in all_parts:
            summaries[p] = BalanceSummary(
                participant=p,
                total_paid=paid_map[p],
                total_owed=owed_map[p],
            )

        # Verify net conservation invariant
        net_sum = sum((s.net_balance for s in summaries.values()), Decimal("0.00"))
        if to_cents(net_sum) != Decimal("0.00"):
            raise RuntimeError(f"Net conservation violation: sum of balances is {net_sum}")

        return summaries
