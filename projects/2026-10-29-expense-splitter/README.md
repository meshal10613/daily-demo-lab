# Expense Splitter & Debt Minimizer 💸

A clean, robust Python library and CLI tool for splitting shared group expenses and calculating the optimal, minimal debt settlement plan.

---

## 🧐 The Problem

When roommates, friends, or coworkers travel or share expenses together (e.g. cabin rentals, grocery runs, restaurant dinners), people pay varying amounts for different subsets of the group.

This commonly leads to:
1. **Lost Pennies & Rounding Errors**: Division like \$100.00 / 3 leaves floating-point inaccuracies or unallocated pennies if not handled with integer-cent precision.
2. **The "Debt Web" Complexity**: If 5 people pay for different items, direct reimbursements can require up to $N(N - 1) / 2 = 10$ separate payments between friends.
3. **Rigid Split Types**: Some bills are split equally, while others involve exact menu items, percentages, or weighted shares.

---

## 💡 The Solution

**Expense Splitter** solves these problems:
- **Penny-Perfect Financial Arithmetic**: Built entirely using Python's `Decimal` module with deterministic remainder distribution. Every cent is accounted for.
- **Cash Flow Minimization Algorithm**: Uses a greedy min-max matching algorithm to reduce group debts to at most **$N - 1$ total transactions**.
- **Versatile Split Modes**:
  - `EQUAL`: Split evenly among all or a designated subset of participants.
  - `EXACT`: Assign explicit dollar amounts to each participant.
  - `PERCENTAGE`: Specify percentage contributions summing to 100%.
  - `SHARES`: Weighted consumption ratios (e.g., 2 shares vs 1 share).
- **Categorized Spending Analytics**: Tracks expenses across categories (Food, Lodging, Transport, etc.) and provides breakdown percentages.
- **Lightweight & Dependency-Free**: Runs entirely on the Python 3 standard library.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+ (tested through Python 3.14).
- No external third-party dependencies required.

### Quick Run

To see the interactive demo of a 4-person weekend mountain trip:

```bash
python run.py demo
# or with Windows Python launcher:
py run.py demo
```

---

## 📖 Usage Examples

### 1. Built-in Trip Demo

```bash
py run.py demo
```

Output:
```text
================================================================
 EXPENSE SPLITTER REPORT: MOUNTAIN CABIN WEEKEND TRIP 
================================================================

Participants (4): Alice, Bob, Charlie, Diana
Total Group Spending: $1,115.50

--- Spending by Category ---
  * Lodging           :    $600.00 (53.8%)
  * Food & Drinks     :    $425.50 (38.1%)
  * Transport         :     $90.00 (8.1%)

--- Expenses Ledger ---
  1. [Lodging] Cabin Airbnb Rental: $600.00 paid by Alice (EQUAL -> All (Alice, Bob, Charlie, Diana))
  2. [Food & Drinks] Supermarket Groceries & Snacks: $185.50 paid by Bob (EQUAL -> All (Alice, Bob, Charlie, Diana))
  3. [Transport] Road Trip Gas & Highway Tolls: $90.00 paid by Charlie (EQUAL -> Alice, Bob, Charlie)
  4. [Food & Drinks] Fine Dining Dinner: $240.00 paid by Diana (EXACT -> Alice, Bob, Charlie, Diana)

--- Net Balances ---
  Participant    Total Paid   Total Owed    Net Balance
  -----------------------------------------------------
  Alice             $600.00      $276.37   +$323.63 (gets back)
  Bob               $185.50      $301.37        -$115.87 (owes)
  Charlie            $90.00      $271.38        -$181.38 (owes)
  Diana             $240.00      $266.38         -$26.38 (owes)

--- Optimal Debt Settlement Plan (Minimal Cash Flow) ---
  1. Charlie pays Alice -> $181.38
  2. Bob pays Alice -> $115.87
  3. Diana pays Alice -> $26.38

================================================================
```

### 2. Quick Split from CLI

Split a single dinner or bill evenly among friends:

```bash
py run.py quick-split --total 120.00 --payer Alice --people Alice Bob Charlie
```

### 3. Loading from a JSON Ledger

```bash
# Text report
py run.py file sample_trip.json

# Structured JSON output for programmatic pipelines
py run.py file sample_trip.json --json
```

### 4. Using as a Python Library

```python
from decimal import Decimal
from expense_splitter import ExpenseGroup, Expense, SplitType, minimize_cash_flow

# Create a group
group = ExpenseGroup(name="Ski Trip")
group.add_participant("Alice")
group.add_participant("Bob")

# Record an expense
group.add_expense(
    Expense(
        description="Lift Tickets",
        payer="Alice",
        amount=Decimal("150.00"),
        split_type=SplitType.EQUAL
    )
)

# Compute balances and settle
balances = group.get_balances()
transfers = minimize_cash_flow(balances)

for t in transfers:
    print(t)  # Bob -> Alice: $75.00
```

---

## 🧪 Running Tests

A comprehensive unit test suite verifies models, rounding algorithms, edge cases, circular debts, and CLI operations:

```bash
python -m unittest discover -s tests -p "test_*.py"
# or
py -m unittest discover -s tests -p "test_*.py"
```

Expected output:
```text
Ran 11 tests in 0.015s

OK
```
