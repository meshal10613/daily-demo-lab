"""CLI interface for JSON Schema Inferrer & Validator."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, List

from schema_infer.core import infer_schema, validate_instance


def load_json_source(source: str) -> Any:
    """Load JSON from file path or STDIN."""
    if source == "-":
        return json.load(sys.stdin)
    with open(source, "r", encoding="utf-8") as f:
        return json.load(f)


def main(args: List[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="json-schema-infer",
        description="Infer and validate JSON Schema Draft-07 models."
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # Infer command
    infer_p = subparsers.add_parser("infer", help="Infer schema from JSON samples")
    infer_p.add_argument("input", help="Path to JSON file or '-' for stdin")
    infer_p.add_argument("-t", "--title", default=None, help="Optional title for the schema")
    infer_p.add_argument("-o", "--output", default=None, help="Output file path (default: stdout)")
    infer_p.add_argument("--indent", type=int, default=2, help="JSON indentation level (default: 2)")
    infer_p.add_argument("--no-format", action="store_true", help="Disable string format inference")
    infer_p.add_argument("--loose-required", action="store_true", help="Do not enforce required properties")

    # Validate command
    val_p = subparsers.add_parser("validate", help="Validate a JSON payload against a schema")
    val_p.add_argument("-s", "--schema", required=True, help="Path to JSON schema file")
    val_p.add_argument("-i", "--input", required=True, help="Path to instance JSON file or '-' for stdin")

    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        return 1

    if parsed.command == "infer":
        try:
            data = load_json_source(parsed.input)
        except Exception as e:
            sys.stderr.write(f"Error reading input JSON: {e}\n")
            return 1

        # If input is a list of objects, we can infer from the records
        samples = data if isinstance(data, list) else [data]
        schema = infer_schema(
            samples,
            title=parsed.title,
            detect_formats=not parsed.no_format,
            strict_required=not parsed.loose_required
        )

        rendered = json.dumps(schema, indent=parsed.indent)
        if parsed.output:
            try:
                with open(parsed.output, "w", encoding="utf-8") as f:
                    f.write(rendered + "\n")
            except Exception as e:
                sys.stderr.write(f"Error writing output: {e}\n")
                return 1
        else:
            print(rendered)
        return 0

    if parsed.command == "validate":
        try:
            schema = load_json_source(parsed.schema)
            instance = load_json_source(parsed.input)
        except Exception as e:
            sys.stderr.write(f"Error reading schema or input: {e}\n")
            return 1

        valid, errors = validate_instance(instance, schema)
        if valid:
            print("SUCCESS: JSON document conforms to the schema.")
            return 0
        else:
            print(f"FAILURE: Document has {len(errors)} validation error(s):", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            return 2

    return 0
