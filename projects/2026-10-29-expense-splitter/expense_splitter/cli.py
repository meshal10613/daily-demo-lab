"""Command-line interface for the Expense Splitter application."""

import argparse
import json
import sys
from decimal import Decimal
from typing import List, Optional
from .calculator import ExpenseGroup
from .minimizer import minimize_cash_flow
from .models import Expense, SplitShare, SplitType
from .storage import load_group_from_file, group_to_dict


def format_currency(val: Decimal) -> str:
    return f"${val:,.2f}"


def build_sample_trip() -> ExpenseGroup:
    """Creates a sample trip with multi-category and varied split scenarios."""
    group = ExpenseGroup(name="Mountain Cabin Weekend Trip")
    for person in ["Alice", "Bob", "Charlie", "Diana"]:
        group.add_participant(person)

    # 1. Cabin Rental: Alice paid $600.00, split equally among all 4 ($150 each)
    group.add_expense(
        Expense(
            description="Cabin Airbnb Rental",
            payer="Alice",
            amount=Decimal("600.00"),
            category="Lodging",
            split_type=SplitType.EQUAL,
        )
    )

    # 2. Grocery run: Bob paid $185.50, split equally among all 4 ($46.38 / $46.37)
    group.add_expense(
        Expense(
            description="Supermarket Groceries & Snacks",
            payer="Bob",
            amount=Decimal("185.50"),
            category="Food & Drinks",
            split_type=SplitType.EQUAL,
        )
    )

    # 3. Gas & Tolls: Charlie paid $90.00, split between Alice, Bob, and Charlie (Diana rode train)
    group.add_expense(
        Expense(
            description="Road Trip Gas & Highway Tolls",
            payer="Charlie",
            amount=Decimal("90.00"),
            category="Transport",
            split_type=SplitType.EQUAL,
            splits=[
                SplitShare("Alice"),
                SplitShare("Bob"),
                SplitShare("Charlie"),
            ],
        )
    )

    # 4. Fancy Dinner: Diana paid $240.00, split by exact wine & steak orders
    group.add_expense(
        Expense(
            description="Fine Dining Dinner",
            payer="Diana",
            amount=Decimal("240.00"),
            category="Food & Drinks",
            split_type=SplitType.EXACT,
            splits=[
                SplitShare("Alice", Decimal("50.00")),
                SplitShare("Bob", Decimal("75.00")),
                SplitShare("Charlie", Decimal("45.00")),
                SplitShare("Diana", Decimal("70.00")),
            ],
        )
    )

    return group


def print_group_report(group: ExpenseGroup) -> None:
    """Renders a formatted text report of the expense group."""
    print("=" * 64)
    print(f" EXPENSE SPLITTER REPORT: {group.name.upper()} ")
    print("=" * 64)

    total_spent = group.get_total_spending()
    print(f"\nParticipants ({len(group.participants)}): {', '.join(group.participants)}")
    print(f"Total Group Spending: {format_currency(total_spent)}")

    # Category breakdown
    print("\n--- Spending by Category ---")
    categories = group.get_category_spending()
    for cat, amt in categories.items():
        pct = (amt / total_spent * Decimal("100.00")) if total_spent > Decimal("0.00") else Decimal("0.00")
        print(f"  * {cat:<18}: {format_currency(amt):>10} ({pct:.1f}%)")

    # Expenses ledger
    print("\n--- Expenses Ledger ---")
    for idx, exp in enumerate(group.expenses, start=1):
        target_str = (
            ", ".join(s.participant for s in exp.splits)
            if exp.splits
            else "All (" + ", ".join(group.participants) + ")"
        )
        print(
            f"  {idx}. [{exp.category}] {exp.description}: "
            f"{format_currency(exp.amount)} paid by {exp.payer} "
            f"({exp.split_type.value} -> {target_str})"
        )

    # Balances
    print("\n--- Net Balances ---")
    balances = group.get_balances()
    header = f"  {'Participant':<12} {'Total Paid':>12} {'Total Owed':>12} {'Net Balance':>14}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    for p in group.participants:
        b = balances[p]
        net_str = format_currency(b.net_balance)
        if b.net_balance > Decimal("0.00"):
            net_display = f"+{net_str} (gets back)"
        elif b.net_balance < Decimal("0.00"):
            net_display = f"-{format_currency(abs(b.net_balance))} (owes)"
        else:
            net_display = " $0.00 (settled)"

        print(
            f"  {b.participant:<12} {format_currency(b.total_paid):>12} "
            f"{format_currency(b.total_owed):>12} {net_display:>22}"
        )

    # Debt Settlement
    print("\n--- Optimal Debt Settlement Plan (Minimal Cash Flow) ---")
    settlements = minimize_cash_flow(balances)
    if not settlements:
        print("  All balances are perfectly settled! No transfers needed.")
    else:
        for idx, s in enumerate(settlements, start=1):
            print(f"  {idx}. {s.debtor} pays {s.creditor} -> {format_currency(s.amount)}")

    print("\n" + "=" * 64)


def handle_demo() -> None:
    group = build_sample_trip()
    print_group_report(group)


def handle_quick_split(total: Decimal, payer: str, people: List[str]) -> None:
    group = ExpenseGroup(name="Quick Split")
    for person in people:
        group.add_participant(person)

    group.add_expense(
        Expense(
            description="Quick Shared Bill",
            payer=payer,
            amount=total,
            split_type=SplitType.EQUAL,
        )
    )
    print_group_report(group)


def handle_file(filepath: str, output_json: bool = False) -> None:
    group = load_group_from_file(filepath)
    if output_json:
        balances = group.get_balances()
        settlements = minimize_cash_flow(balances)
        out = {
            "group": group_to_dict(group),
            "total_spending": str(group.get_total_spending()),
            "category_spending": {k: str(v) for k, v in group.get_category_spending().items()},
            "balances": {
                p: {
                    "paid": str(b.total_paid),
                    "owed": str(b.total_owed),
                    "net": str(b.net_balance),
                }
                for p, b in balances.items()
            },
            "settlements": [
                {
                    "debtor": s.debtor,
                    "creditor": s.creditor,
                    "amount": str(s.amount),
                }
                for s in settlements
            ],
        }
        print(json.dumps(out, indent=2))
    else:
        print_group_report(group)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="expense-splitter",
        description="Fair bill and shared expense splitting with minimal debt settlement.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Subcommand: demo
    subparsers.add_parser("demo", help="Run the built-in multi-person trip demonstration.")

    # Subcommand: quick-split
    qs = subparsers.add_parser("quick-split", help="Quickly split a single bill evenly.")
    qs.add_argument("--total", required=True, type=Decimal, help="Total bill amount (e.g. 120.50)")
    qs.add_argument("--payer", required=True, help="Name of the person who paid")
    qs.add_argument("--people", required=True, nargs="+", help="Names of all participants")

    # Subcommand: file
    f_parser = subparsers.add_parser("file", help="Load an expense group ledger from a JSON file.")
    f_parser.add_argument("path", help="Path to the JSON ledger file")
    f_parser.add_argument("--json", action="store_true", help="Output calculated results in JSON format")

    args = parser.parse_args(argv)

    if not args.command or args.command == "demo":
        handle_demo()
        return 0

    if args.command == "quick-split":
        handle_quick_split(args.total, args.payer, args.people)
        return 0

    if args.command == "file":
        handle_file(args.path, output_json=args.json)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
