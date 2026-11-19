"""Core logic for parsing, auditing, diffing, and formatting .env files."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Common placeholder values that indicate missing configuration
DEFAULT_PLACEHOLDERS = {
    "changeme",
    "change_me",
    "change-me",
    "your_api_key",
    "your-api-key",
    "your_token",
    "your_password",
    "todo",
    "secret",
    "password",
    "admin",
    "root",
    "123456",
    "placeholder",
    "example",
    "null",
    "none",
}

# Keywords indicating that a key likely holds sensitive information
SENSITIVE_KEY_PATTERNS = [
    re.compile(r"(secret|password|passwd|token|private|key|auth|credential)", re.IGNORECASE)
]


@dataclass
class EnvEntry:
    key: str
    value: str
    raw_line: str
    line_number: int
    is_export: bool = False
    comment: Optional[str] = None


@dataclass
class AuditIssue:
    severity: str  # "ERROR", "WARNING", "INFO"
    key: str
    line_number: int
    message: str


@dataclass
class DiffResult:
    missing_in_target: List[str] = field(default_factory=list)
    extra_in_target: List[str] = field(default_factory=list)
    identical_to_template: List[Tuple[str, str]] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.missing_in_target or self.identical_to_template)


class EnvParser:
    """Parses .env file content according to standard dotenv rules."""

    LINE_REGEX = re.compile(
        r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$"
    )

    @classmethod
    def parse(cls, content: str) -> Dict[str, EnvEntry]:
        entries: Dict[str, EnvEntry] = {}
        lines = content.splitlines()

        for idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            match = cls.LINE_REGEX.match(raw_line)
            if not match:
                continue

            key = match.group(1)
            val_part = match.group(2).strip()
            is_export = raw_line.strip().startswith("export ")
            comment = None

            # Handle quoted strings
            if (val_part.startswith('"') and '"' in val_part[1:]) or (
                val_part.startswith("'") and "'" in val_part[1:]
            ):
                quote_char = val_part[0]
                end_idx = val_part.find(quote_char, 1)
                val = val_part[1:end_idx]
                remainder = val_part[end_idx + 1 :].strip()
                if remainder.startswith("#"):
                    comment = remainder[1:].strip()
            else:
                # Unquoted: split inline comments
                if " #" in val_part:
                    val, comment_part = val_part.split(" #", 1)
                    val = val.strip()
                    comment = comment_part.strip()
                elif val_part.startswith("#"):
                    val = ""
                    comment = val_part[1:].strip()
                else:
                    val = val_part

            entries[key] = EnvEntry(
                key=key,
                value=val,
                raw_line=raw_line,
                line_number=idx,
                is_export=is_export,
                comment=comment,
            )

        return entries


class EnvAuditor:
    """Audits parsed environment entries for vulnerabilities, mistakes, and bad hygiene."""

    @classmethod
    def audit(cls, entries: Dict[str, EnvEntry]) -> List[AuditIssue]:
        issues: List[AuditIssue] = []

        for key, entry in entries.items():
            val = entry.value.strip()
            val_lower = val.lower()

            # 1. Empty value check
            if not val:
                issues.append(
                    AuditIssue(
                        severity="WARNING",
                        key=key,
                        line_number=entry.line_number,
                        message="Empty environment variable value",
                    )
                )
                continue

            # 2. Known placeholder values check
            if val_lower in DEFAULT_PLACEHOLDERS:
                issues.append(
                    AuditIssue(
                        severity="ERROR",
                        key=key,
                        line_number=entry.line_number,
                        message=f"Placeholder value '{val}' detected",
                    )
                )

            # 3. Check for insecure URLs in production keys
            if "URL" in key.upper() and val.startswith("http://"):
                issues.append(
                    AuditIssue(
                        severity="WARNING",
                        key=key,
                        line_number=entry.line_number,
                        message="Insecure HTTP protocol used in URL",
                    )
                )

            # 4. Sensitive keys with weak or trivial length
            is_sensitive = any(p.search(key) for p in SENSITIVE_KEY_PATTERNS)
            if is_sensitive and len(val) < 8 and val_lower not in DEFAULT_PLACEHOLDERS:
                issues.append(
                    AuditIssue(
                        severity="WARNING",
                        key=key,
                        line_number=entry.line_number,
                        message="Sensitive variable value is very short (< 8 characters)",
                    )
                )

        return sorted(issues, key=lambda x: (x.line_number, x.severity))


class EnvComparator:
    """Compares target .env against reference template .env.example."""

    @classmethod
    def diff(
        cls, target: Dict[str, EnvEntry], template: Dict[str, EnvEntry]
    ) -> DiffResult:
        missing_in_target = [k for k in template if k not in target]
        extra_in_target = [k for k in target if k not in template]

        # Check if target simply copied template's default values
        identical_to_template = []
        for k in template:
            if k in target and template[k].value != "":
                if target[k].value == template[k].value:
                    identical_to_template.append((k, target[k].value))

        return DiffResult(
            missing_in_target=sorted(missing_in_target),
            extra_in_target=sorted(extra_in_target),
            identical_to_template=sorted(identical_to_template, key=lambda x: x[0]),
        )


class EnvMasker:
    """Masks sensitive values for safe sharing or logs."""

    @staticmethod
    def mask_value(val: str) -> str:
        if not val:
            return ""
        if len(val) <= 4:
            return "****"
        if len(val) <= 10:
            return f"{val[:1]}****{val[-1:]}"
        return f"{val[:2]}****{val[-2:]}"

    @classmethod
    def mask_all(
        cls, entries: Dict[str, EnvEntry], mask_all_keys: bool = False
    ) -> Dict[str, str]:
        masked: Dict[str, str] = {}
        for key, entry in entries.items():
            is_sensitive = mask_all_keys or any(
                p.search(key) for p in SENSITIVE_KEY_PATTERNS
            )
            if is_sensitive:
                masked[key] = cls.mask_value(entry.value)
            else:
                masked[key] = entry.value
        return masked


class EnvFormatter:
    """Formats and sorts environment files canonically."""

    @classmethod
    def format_entries(cls, entries: Dict[str, EnvEntry], sort_keys: bool = True) -> str:
        keys = sorted(entries.keys()) if sort_keys else list(entries.keys())
        output_lines: List[str] = []

        for k in keys:
            entry = entries[k]
            prefix = "export " if entry.is_export else ""
            val = entry.value
            # Wrap in quotes if spaces or special characters exist
            if " " in val or "\n" in val or "#" in val:
                formatted_val = f'"{val}"'
            else:
                formatted_val = val

            line = f"{prefix}{k}={formatted_val}"
            if entry.comment:
                line += f" # {entry.comment}"
            output_lines.append(line)

        return "\n".join(output_lines) + "\n"
