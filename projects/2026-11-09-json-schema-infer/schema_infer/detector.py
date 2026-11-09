"""String format pattern matchers."""
import re

PATTERNS = {
    "uuid": re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"),
    "date-time": re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"),
    "date": re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    "email": re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$dev|(\.[a-zA-Z]{2,})$"),
    "ipv4": re.compile(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"),
    "uri": re.compile(r"^(?:https?|ftp|file)://[^\s/$.?#].[^\s]*$"),
}

# Simplified email regex
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def detect_string_format(val: str) -> str | None:
    """Detect standard JSON schema string formats."""
    if not val or len(val) > 256:
        return None
    if PATTERNS["uuid"].match(val):
        return "uuid"
    if PATTERNS["date-time"].match(val):
        return "date-time"
    if PATTERNS["date"].match(val):
        return "date"
    if PATTERNS["ipv4"].match(val):
        return "ipv4"
    if EMAIL_REGEX.match(val):
        return "email"
    if PATTERNS["uri"].match(val):
        return "uri"
    return None
