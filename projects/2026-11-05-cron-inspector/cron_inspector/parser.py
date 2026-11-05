"""Cron expression parser and syntax validator."""
from dataclasses import dataclass
from typing import Set, Tuple, Dict
import re

MONTH_NAMES = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
}

DAY_NAMES = {
    "SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6
}

FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day_of_month": (1, 31),
    "month": (1, 12),
    "day_of_week": (0, 7)  # 0 and 7 are both Sunday
}


class CronParseError(ValueError):
    """Raised when a cron expression is syntactically invalid."""
    pass


@dataclass(frozen=True)
class CronField:
    name: str
    raw: str
    values: Tuple[int, ...]

    def matches(self, val: int) -> bool:
        if self.name == "day_of_week":
            # Normalize 7 to 0 for Sunday
            normalized_val = 0 if val == 7 else val
            return normalized_val in self.values or (7 in self.values and normalized_val == 0)
        return val in self.values


@dataclass(frozen=True)
class CronExpression:
    raw: str
    minute: CronField
    hour: CronField
    day_of_month: CronField
    month: CronField
    day_of_week: CronField

    def as_dict(self) -> Dict[str, dict]:
        return {
            "minute": {"raw": self.minute.raw, "values": list(self.minute.values)},
            "hour": {"raw": self.hour.raw, "values": list(self.hour.values)},
            "day_of_month": {"raw": self.day_of_month.raw, "values": list(self.day_of_month.values)},
            "month": {"raw": self.month.raw, "values": list(self.month.values)},
            "day_of_week": {"raw": self.day_of_week.raw, "values": list(self.day_of_week.values)},
        }


def _replace_names(token: str, name_map: Dict[str, int]) -> str:
    upper_token = token.upper()
    for name, num in name_map.items():
        upper_token = re.sub(rf'\b{name}\b', str(num), upper_token)
    return upper_token


def _parse_segment(segment: str, min_v: int, max_v: int, field_name: str) -> Set[int]:
    segment = segment.strip()
    if not segment:
        raise CronParseError(f"{field_name}: empty sub-expression encountered")

    step = 1
    if "/" in segment:
        parts = segment.split("/")
        if len(parts) != 2:
            raise CronParseError(f"{field_name}: invalid step expression '{segment}'")
        range_part, step_str = parts
        if not step_str.isdigit() or int(step_str) <= 0:
            raise CronParseError(f"{field_name}: step value must be a positive integer in '{segment}'")
        step = int(step_str)
    else:
        range_part = segment

    if range_part == "*" or range_part == "?":
        start_v, end_v = min_v, max_v
    elif "-" in range_part:
        dash_parts = range_part.split("-")
        if len(dash_parts) != 2:
            raise CronParseError(f"{field_name}: invalid range expression '{range_part}'")
        s_str, e_str = dash_parts
        if not (s_str.isdigit() and e_str.isdigit()):
            raise CronParseError(f"{field_name}: non-numeric range '{range_part}'")
        start_v, end_v = int(s_str), int(e_str)
        if start_v > end_v:
            raise CronParseError(f"{field_name}: range start {start_v} > end {end_v}")
    else:
        if not range_part.isdigit():
            raise CronParseError(f"{field_name}: invalid literal '{range_part}'")
        val = int(range_part)
        if "/" in segment:
            start_v, end_v = val, max_v
        else:
            if val < min_v or val > max_v:
                raise CronParseError(f"{field_name}: value {val} out of bounds ({min_v}-{max_v})")
            return {val}

    if start_v < min_v or end_v > max_v:
        raise CronParseError(f"{field_name}: range {start_v}-{end_v} out of bounds ({min_v}-{max_v})")

    return set(range(start_v, end_v + 1, step))


def parse_field(raw_field: str, field_name: str) -> CronField:
    min_v, max_v = FIELD_RANGES[field_name]
    transformed = raw_field.strip()

    if field_name == "month":
        transformed = _replace_names(transformed, MONTH_NAMES)
    elif field_name == "day_of_week":
        transformed = _replace_names(transformed, DAY_NAMES)

    values: Set[int] = set()
    segments = transformed.split(",")
    for seg in segments:
        parsed_vals = _parse_segment(seg, min_v, max_v, field_name)
        values.update(parsed_vals)

    if field_name == "day_of_week":
        # Standardize 7 (Sunday) to 0, keeping set clean
        normalized = set()
        for v in values:
            normalized.add(0 if v == 7 else v)
        values = normalized

    if not values:
        raise CronParseError(f"{field_name}: yielded no valid integer values")

    sorted_values = tuple(sorted(values))
    return CronField(name=field_name, raw=raw_field.strip(), values=sorted_values)


def parse_cron(expression: str) -> CronExpression:
    tokens = expression.strip().split()
    if len(tokens) != 5:
        raise CronParseError(
            f"Expected 5 cron fields (minute, hour, dom, month, dow), but got {len(tokens)}: '{expression}'"
        )

    minute_f = parse_field(tokens[0], "minute")
    hour_f = parse_field(tokens[1], "hour")
    dom_f = parse_field(tokens[2], "day_of_month")
    month_f = parse_field(tokens[3], "month")
    dow_f = parse_field(tokens[4], "day_of_week")

    return CronExpression(
        raw=expression.strip(),
        minute=minute_f,
        hour=hour_f,
        day_of_month=dom_f,
        month=month_f,
        day_of_week=dow_f
    )
