"""Calculate upcoming occurrences for a cron expression."""
import calendar
from datetime import datetime, timedelta
from typing import List, Generator
from .parser import CronExpression


def _day_matches(expr: CronExpression, dt: datetime) -> bool:
    # Standard cron rule: if both DOM and DOW are specified (neither is '*'),
    # either condition matching triggers the run (OR logic). If one is '*', the other governs.
    dom_wildcard = expr.day_of_month.raw in ("*", "?")
    dow_wildcard = expr.day_of_week.raw in ("*", "?")

    # Python weekday(): Monday is 0, Sunday is 6. In Cron: Sunday is 0, Saturday is 6.
    cron_dow = (dt.weekday() + 1) % 7
    dom_match = expr.day_of_month.matches(dt.day)
    dow_match = expr.day_of_week.matches(cron_dow)

    if dom_wildcard and dow_wildcard:
        return True
    if not dom_wildcard and not dow_wildcard:
        return dom_match or dow_match
    if not dom_wildcard:
        return dom_match
    return dow_match


def cron_schedule_generator(expr: CronExpression, start_time: datetime) -> Generator[datetime, None, None]:
    """Yields consecutive future datetime occurrences matching the cron expression."""
    # Advance past the start second/microsecond to the next exact whole minute
    current = start_time.replace(second=0, microsecond=0) + timedelta(minutes=1)
    max_iterations = 525_600 * 5  # Up to 5 full calendar years of minute steps
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # Fast-forward month if not matching
        if not expr.month.matches(current.month):
            # Move to the 1st of next month at 00:00
            if current.month == 12:
                current = datetime(current.year + 1, 1, 1, 0, 0)
            else:
                current = datetime(current.year, current.month + 1, 1, 0, 0)
            continue

        # Fast-forward day if not matching or invalid date (e.g., Feb 30)
        days_in_month = calendar.monthrange(current.year, current.month)[1]
        if current.day > days_in_month or not _day_matches(expr, current):
            current = (current + timedelta(days=1)).replace(hour=0, minute=0)
            continue

        # Fast-forward hour if not matching
        if not expr.hour.matches(current.hour):
            current = (current + timedelta(hours=1)).replace(minute=0)
            continue

        # Check minute
        if expr.minute.matches(current.minute):
            yield current

        current += timedelta(minutes=1)


def get_next_runs(expr: CronExpression, base_time: datetime = None, count: int = 5) -> List[datetime]:
    """Return the next `count` datetimes starting from `base_time`."""
    if base_time is None:
        base_time = datetime.now()
    if count <= 0:
        return []

    results: List[datetime] = []
    for dt in cron_schedule_generator(expr, base_time):
        results.append(dt)
        if len(results) >= count:
            break
    return results
