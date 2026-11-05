# Cron Inspector

> A lightweight, zero-dependency developer utility to parse, validate, explain in plain English, and forecast execution schedules for standard 5-field cron expressions.

---

## Problem

Cron syntax (`* * * * *`) is ubiquitous in backend engineering, task schedulers, CI/CD pipelines, and cloud orchestration. However:
- Small syntax mistakes (such as Sunday indexed as `0` vs `7`, or invalid step values) often go unnoticed until runtime failures.
- Reading complex combinations of ranges, lists, and steps (`*/15 9-17 1,15 * 1-5`) is error-prone for humans.
- Developers frequently rely on ad-hoc web tools to verify next execution timestamps, leaking sensitive internal scheduling conventions or requiring internet access.

## Features

- **Zero External Dependencies**: Pure Python 3 standard library.
- **Full Standard 5-Field Support**: `minute`, `hour`, `day of month`, `month`, and `day of week`.
- **Rich Syntax Support**: Ranges (`1-5`), lists (`1,15,30`), step intervals (`*/10`, `1-20/2`), and text aliases (`JAN-DEC`, `SUN-SAT`). Both `0` and `7` are correctly recognized as Sunday.
- **Human Explanation Engine**: Translates complex cron schedules into clean, readable English sentences.
- **Occurrence Forecaster**: Computes the exact future timestamps (next *N* runs) matching the expression starting from any reference time.
- **Machine-Readable CLI**: Supports formatted text terminal output and `--json` for pipeline integration.

---

## Setup

No third-party packages are required. Python 3.8+ is supported.

```bash
# Verify Python installation
python3 --version

# Make run script executable (optional)
chmod +x run.py
```

---

## Usage

### 1. Command Line Interface

#### Explain a cron expression
```bash
python3 run.py explain "*/15 9-17 * * 1-5"
```
Output:
```text
Cron Expression: */15 9-17 * * 1-5
Explanation    : Every 15 minutes, from 09:00 through 17:00, Monday through Friday

Field Details:
  Minute       : */15 (0, 15, 30, 45)
  Hour         : 9-17 (9, 10, 11, 12, 13, 14, 15, 16, 17)
  Day of Month : * (any day of month)
  Month        : * (every month)
  Day of Week  : 1-5 (Monday through Friday)
```

#### Forecast upcoming executions
```bash
python3 run.py next "0 0 1,15 * *" --count 3 --from "2026-11-05 10:00:00"
```
Output:
```text
Upcoming 3 execution times for '0 0 1,15 * *':
  1. 2026-11-15 00:00:00 (in 9 days, 14:00:00)
  2. 2026-12-01 00:00:00 (in 25 days, 14:00:00)
  3. 2026-12-15 00:00:00 (in 39 days, 14:00:00)
```

#### Validate syntax
```bash
python3 run.py validate "60 * * * *"
```
Output:
```text
Invalid cron expression: Minute '60' is out of bounds (0-59)
```

#### Output as JSON
```bash
python3 run.py explain "0 22 * * 0" --json
```

### 2. Python API

```python
from datetime import datetime
from cron_inspector.parser import parse_cron
from cron_inspector.humanizer import humanize_cron
from cron_inspector.scheduler import get_next_runs

expr = parse_cron("30 4 * * 1-5")
print(humanize_cron(expr))
# "At 04:30, Monday through Friday"

now = datetime(2026, 11, 5, 12, 0)
for run_time in get_next_runs(expr, base_time=now, count=3):
    print(run_time.isoformat())
```

---

## Running Tests

Execute the unit tests using Python's standard `unittest` module:

```bash
python3 -m unittest discover -s tests -v
```
