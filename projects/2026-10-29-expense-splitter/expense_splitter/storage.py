"""JSON serialization and deserialization for expense groups."""

import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Union
from .calculator import ExpenseGroup
from .models import Expense, SplitShare, SplitType, to_cents


def group_to_dict(group: ExpenseGroup) -> Dict[str, Any]:
    """Serializes an ExpenseGroup into a standard Python dictionary."""
    return {
        "name": group.name,
        "participants": group.participants,
        "expenses": [
            {
                "description": exp.description,
                "payer": exp.payer,
                "amount": str(exp.amount),
                "category": exp.category,
                "split_type": exp.split_type.value,
                "splits": [
                    {
                        "participant": s.participant,
                        "value": str(s.value) if s.value is not None else None,
                    }
                    for s in exp.splits
                ],
            }
            for exp in group.expenses
        ],
    }


def save_group_to_dict(group: ExpenseGroup) -> Dict[str, Any]:
    return group_to_dict(group)


def save_group_to_file(group: ExpenseGroup, path: Union[str, Path]) -> None:
    data = group_to_dict(group)
    path = Path(path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_group_from_dict(data: Dict[str, Any]) -> ExpenseGroup:
    """Deserializes an ExpenseGroup from a Python dictionary."""
    group = ExpenseGroup(name=data.get("name", "Group Ledger"))

    for p in data.get("participants", []):
        group.add_participant(p)

    for exp_raw in data.get("expenses", []):
        splits = []
        for s in exp_raw.get("splits", []):
            val = Decimal(str(s["value"])) if s.get("value") is not None else None
            splits.append(SplitShare(participant=s["participant"], value=val))

        split_type = SplitType(exp_raw.get("split_type", "EQUAL"))
        expense = Expense(
            description=exp_raw["description"],
            payer=exp_raw["payer"],
            amount=Decimal(str(exp_raw["amount"])),
            category=exp_raw.get("category", "General"),
            split_type=split_type,
            splits=splits,
        )
        group.add_expense(expense)

    return group


def load_group_from_file(path: Union[str, Path]) -> ExpenseGroup:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return load_group_from_dict(data)
