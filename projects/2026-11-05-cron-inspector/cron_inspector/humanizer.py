"""Generates natural English descriptions of parsed cron expressions."""
from typing import Sequence
from .parser import CronExpression

DOW_LABELS = {
    0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday",
    4: "Thursday", 5: "Friday", 6: "Saturday"
}

MONTH_LABELS = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}


def _format_ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _is_consecutive(vals: Sequence[int]) -> bool:
    if len(vals) <= 1:
        return False
    return all(vals[i] + 1 == vals[i + 1] for i in range(len(vals) - 1))


def _describe_time(minute_field, hour_field) -> str:
    m_raw, h_raw = minute_field.raw, hour_field.raw
    m_vals, h_vals = minute_field.values, hour_field.values

    # Every minute
    if m_raw in ("*", "*/1") and h_raw == "*":
        return "Every minute"

    # Every N minutes
    if m_raw.startswith("*/") and h_raw == "*":
        step = m_raw.split("/")[1]
        return f"Every {step} minutes"

    # Specific minutes every hour
    if h_raw == "*":
        if len(m_vals) == 1:
            return f"At minute {m_vals[0]} of every hour"
        mins_str = ", ".join(str(m) for m in m_vals)
        return f"At minutes {mins_str} of every hour"

    # Specific hour(s) and minute(s)
    if len(m_vals) == 1 and len(h_vals) == 1:
        return f"At {h_vals[0]:02d}:{m_vals[0]:02d}"

    if m_raw.startswith("*/") and len(h_vals) > 1 and _is_consecutive(h_vals):
        step = m_raw.split("/")[1]
        return f"Every {step} minutes, between {h_vals[0]:02d}:00 and {h_vals[-1]:02d}:59"

    if len(m_vals) == 1 and _is_consecutive(h_vals):
        return f"At {m_vals[0]:02d} minutes past the hour, from {h_vals[0]:02d}:00 through {h_vals[-1]:02d}:00"

    hrs_fmt = ", ".join(f"{h:02d}:00" for h in h_vals)
    mins_fmt = ", ".join(f":{m:02d}" for m in m_vals)
    return f"At minutes [{mins_fmt}] of hours [{hrs_fmt}]"


def _describe_dow(dow_field) -> str:
    if dow_field.raw in ("*", "?") and len(dow_field.values) == 7:
        return ""
    vals = dow_field.values
    if vals == (1, 2, 3, 4, 5):
        return "Monday through Friday"
    if vals == (0, 6):
        return "Saturday and Sunday"
    if _is_consecutive(vals):
        return f"{DOW_LABELS[vals[0]]} through {DOW_LABELS[vals[-1]]}"
    return ", ".join(DOW_LABELS[v] for v in vals)


def _describe_dom(dom_field) -> str:
    if dom_field.raw in ("*", "?") and len(dom_field.values) == 31:
        return ""
    vals = dom_field.values
    if _is_consecutive(vals):
        return f"between the {_format_ordinal(vals[0])} and {_format_ordinal(vals[-1])} of the month"
    if len(vals) == 1:
        return f"on the {_format_ordinal(vals[0])} of the month"
    return "on the " + ", ".join(_format_ordinal(v) for v in vals) + " of the month"


def _describe_month(month_field) -> str:
    if month_field.raw in ("*", "?") and len(month_field.values) == 12:
        return ""
    vals = month_field.values
    if _is_consecutive(vals):
        return f"in {MONTH_LABELS[vals[0]]} through {MONTH_LABELS[vals[-1]]}"
    if len(vals) == 1:
        return f"in {MONTH_LABELS[vals[0]]}"
    return "in " + ", ".join(MONTH_LABELS[v] for v in vals)


def humanize_cron(expr: CronExpression) -> str:
    time_desc = _describe_time(expr.minute, expr.hour)
    dom_desc = _describe_dom(expr.day_of_month)
    dow_desc = _describe_dow(expr.day_of_week)
    month_desc = _describe_month(expr.month)

    clauses = [time_desc]
    if dom_desc:
        clauses.append(dom_desc)
    if dow_desc:
        clauses.append(dow_desc)
    if month_desc:
        clauses.append(month_desc)

    sentence = ", ".join(clauses)
    # Ensure proper sentence capitalization
    return sentence[0].upper() + sentence[1:] if sentence else "Always"
