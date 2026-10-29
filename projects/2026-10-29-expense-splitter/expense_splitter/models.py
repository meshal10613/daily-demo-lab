"""Data models and validation for expense splitting."""

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Dict, List, Optional


class SplitType(str, Enum):
    EQUAL = "EQUAL"
    EXACT = "EXACT"
    PERCENTAGE = "PERCENTAGE"
    SHARES = "SHARES"


TWO_PLACES = Decimal("0.01")


def to_cents(amount: Decimal) -> Decimal:
    """Quantize a Decimal amount to standard 2 decimal places."""
    return amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Participant:
    """Represents an individual participating in shared expenses."""
    name: str

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Participant name cannot be blank.")
        object.__setattr__(self, "name", self.name.strip())


@dataclass
class SplitShare:
    """Represents a split allocation parameter for a participant."""
    participant: str
    value: Optional[Decimal] = None  # Exact amount, percentage (0-100), or share weight


@dataclass
class Expense:
    """Represents a single expense record."""
    description: str
    payer: str
    amount: Decimal
    category: str = "General"
    split_type: SplitType = SplitType.EQUAL
    splits: List[SplitShare] = field(default_factory=list)

    def __post_init__(self):
        if not self.description or not self.description.strip():
            raise ValueError("Expense description cannot be empty.")
        if not self.payer or not self.payer.strip():
            raise ValueError("Expense payer cannot be empty.")

        # Ensure amount is a positive Decimal quantized to 2 decimal places
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))
        self.amount = to_cents(self.amount)

        if self.amount <= Decimal("0.00"):
            raise ValueError(f"Expense amount must be greater than zero. Got {self.amount}")

        self.category = self.category.strip() or "General"

    def compute_individual_shares(self, all_participants: List[str]) -> Dict[str, Decimal]:
        """
        Calculates each participant's exact share in cents.
        Guarantees that sum(shares.values()) == self.amount (no lost cents).
        """
        target_participants = [s.participant for s in self.splits] if self.splits else all_participants
        if not target_participants:
            raise ValueError(f"No participants to split expense '{self.description}' across.")

        # Ensure all participants exist
        invalid = [p for p in target_participants if p not in all_participants]
        if invalid:
            raise ValueError(f"Unknown participants in expense split: {invalid}")

        n = len(target_participants)
        shares: Dict[str, Decimal] = {}

        if self.split_type == SplitType.EQUAL:
            base_share = (self.amount / Decimal(n)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            remainder = self.amount - (base_share * Decimal(n))

            # Distribute base share
            for p in target_participants:
                shares[p] = base_share

            # Adjust remainder cents (+0.01 or -0.01) across participants until sum matches
            cent = Decimal("0.01") if remainder > 0 else Decimal("-0.01")
            remainder_steps = int(abs(remainder) / Decimal("0.01"))
            for i in range(remainder_steps):
                p = target_participants[i % n]
                shares[p] += cent

        elif self.split_type == SplitType.EXACT:
            if len(self.splits) != n:
                raise ValueError("EXACT split requires an explicit amount for each target participant.")
            total_allocated = Decimal("0.00")
            for s in self.splits:
                if s.value is None or s.value < Decimal("0.00"):
                    raise ValueError(f"Exact share for {s.participant} must be non-negative.")
                val = to_cents(s.value)
                shares[s.participant] = val
                total_allocated += val

            if total_allocated != self.amount:
                raise ValueError(
                    f"Sum of exact splits ({total_allocated}) does not match expense amount ({self.amount})."
                )

        elif self.split_type == SplitType.PERCENTAGE:
            total_pct = sum(s.value for s in self.splits if s.value is not None)
            if to_cents(total_pct) != Decimal("100.00"):
                raise ValueError(f"Percentage splits must sum to 100.00. Got {total_pct}")

            total_allocated = Decimal("0.00")
            for s in self.splits:
                share_amount = to_cents((self.amount * s.value) / Decimal("100.00"))
                shares[s.participant] = share_amount
                total_allocated += share_amount

            # Compensate for rounding cent difference
            diff = self.amount - total_allocated
            if diff != Decimal("0.00"):
                cent = Decimal("0.01") if diff > 0 else Decimal("-0.01")
                steps = int(abs(diff) / Decimal("0.01"))
                for i in range(steps):
                    p = target_participants[i % n]
                    shares[p] += cent

        elif self.split_type == SplitType.SHARES:
            total_weight = sum(s.value for s in self.splits if s.value is not None)
            if total_weight <= Decimal("0.00"):
                raise ValueError(f"Total shares weight must be greater than zero. Got {total_weight}")

            total_allocated = Decimal("0.00")
            for s in self.splits:
                share_amount = to_cents((self.amount * s.value) / total_weight)
                shares[s.participant] = share_amount
                total_allocated += share_amount

            diff = self.amount - total_allocated
            if diff != Decimal("0.00"):
                cent = Decimal("0.01") if diff > 0 else Decimal("-0.01")
                steps = int(abs(diff) / Decimal("0.01"))
                for i in range(steps):
                    p = target_participants[i % n]
                    shares[p] += cent

        # Verification invariant: total sum of shares MUST equal total expense amount
        if sum(shares.values()) != self.amount:
            raise RuntimeError(f"Internal calculation error: {sum(shares.values())} != {self.amount}")

        return shares
