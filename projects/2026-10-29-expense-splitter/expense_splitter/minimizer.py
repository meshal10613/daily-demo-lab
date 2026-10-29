"""Minimal debt settlement algorithm using greedy cash-flow minimization."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List
from .calculator import BalanceSummary
from .models import to_cents


@dataclass(frozen=True)
class SettlementTransaction:
    """Represents a direct payment required from debtor to creditor."""
    debtor: str
    creditor: str
    amount: Decimal

    def __str__(self) -> str:
        return f"{self.debtor} -> {self.creditor}: ${self.amount:,.2f}"


def minimize_cash_flow(balances: Dict[str, BalanceSummary]) -> List[SettlementTransaction]:
    """
    Computes an optimal, minimal set of transactions to settle all debts.

    Uses a greedy matching strategy that pairs the maximum debtor with the maximum creditor,
    reducing the overall transaction count to at most (N - 1) transactions while
    guaranteeing that every participant's net balance reaches zero.
    """
    # Separate into positive (creditors) and negative (debtors) balances
    creditors: List[List] = []
    debtors: List[List] = []

    for summary in balances.values():
        net = to_cents(summary.net_balance)
        if net > Decimal("0.00"):
            creditors.append([summary.participant, net])
        elif net < Decimal("0.00"):
            debtors.append([summary.participant, abs(net)])

    transactions: List[SettlementTransaction] = []

    while creditors and debtors:
        # Sort so we always match largest debtor with largest creditor
        creditors.sort(key=lambda x: x[1], reverse=True)
        debtors.sort(key=lambda x: x[1], reverse=True)

        creditor_name, credit_amt = creditors[0]
        debtor_name, debt_amt = debtors[0]

        transfer_amt = min(credit_amt, debt_amt)

        transactions.append(
            SettlementTransaction(
                debtor=debtor_name,
                creditor=creditor_name,
                amount=transfer_amt,
            )
        )

        # Update remaining amounts
        remaining_credit = to_cents(credit_amt - transfer_amt)
        remaining_debt = to_cents(debt_amt - transfer_amt)

        if remaining_credit == Decimal("0.00"):
            creditors.pop(0)
        else:
            creditors[0][1] = remaining_credit

        if remaining_debt == Decimal("0.00"):
            debtors.pop(0)
        else:
            debtors[0][1] = remaining_debt

    return transactions
