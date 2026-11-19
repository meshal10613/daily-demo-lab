"""Command line interface for EnvGuard."""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

from .core import EnvAuditor, EnvComparator, EnvFormatter, EnvMasker, EnvParser


def read_file(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def cmd_check(args: argparse.Namespace) -> int:
    try:
        content = read_file(args.file)
    except FileNotFoundError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    entries = EnvParser.parse(content)
    issues = EnvAuditor.audit(entries)

    if args.json:
        output = {
            "file": args.file,
            "total_entries": len(entries),
            "issues": [
                {
                    "severity": i.severity,
                    "key": i.key,
                    "line": i.line_number,
                    "message": i.message,
                }
                for i in issues
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Inspecting '{args.file}' ({len(entries)} variables found)...")
        if not issues:
            print("✓ No issues found. Clean configuration!")
        else:
            for i in issues:
                icon = "❌" if i.severity == "ERROR" else "⚠️"
                print(
                    f"  {icon} [{i.severity}] Line {i.line_number}: Key '{i.key}' - {i.message}"
                )
            print(f"\nTotal issues found: {len(issues)}")

    has_errors = any(i.severity == "ERROR" for i in issues)
    if args.strict and issues:
        return 1
    return 1 if has_errors else 0


def cmd_diff(args: argparse.Namespace) -> int:
    try:
        target_content = read_file(args.target)
        template_content = read_file(args.template)
    except FileNotFoundError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    target_entries = EnvParser.parse(target_content)
    template_entries = EnvParser.parse(template_content)

    result = EnvComparator.diff(target_entries, template_entries)

    if args.json:
        output = {
            "target": args.target,
            "template": args.template,
            "missing_in_target": result.missing_in_target,
            "extra_in_target": result.extra_in_target,
            "identical_to_template": [
                {"key": k, "value": v} for k, v in result.identical_to_template
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Comparing '{args.target}' against template '{args.template}'...")
        if not result.has_issues and not result.extra_in_target:
            print("✓ Target perfectly satisfies template with no drift.")
            return 0

        if result.missing_in_target:
            print("\n❌ Missing keys required by template:")
            for k in result.missing_in_target:
                print(f"   - {k}")

        if result.identical_to_template:
            print("\n⚠️  Keys with unmodified template defaults:")
            for k, val in result.identical_to_template:
                print(f"   - {k} = '{val}'")

        if result.extra_in_target:
            print("\nℹ️  Extra keys present in target but not in template:")
            for k in result.extra_in_target:
                print(f"   + {k}")

    return 1 if result.missing_in_target else 0


def cmd_mask(args: argparse.Namespace) -> int:
    try:
        content = read_file(args.file)
    except FileNotFoundError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    entries = EnvParser.parse(content)
    masked = EnvMasker.mask_all(entries, mask_all_keys=args.all)

    lines = []
    for k, v in sorted(masked.items()):
        lines.append(f"{k}={v}")
    output_text = "\n".join(lines) + "\n"

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"Masked env written to {args.output}")
    else:
        sys.stdout.write(output_text)
    return 0


def cmd_format(args: argparse.Namespace) -> int:
    try:
        content = read_file(args.file)
    except FileNotFoundError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    entries = EnvParser.parse(content)
    formatted = EnvFormatter.format_entries(entries, sort_keys=not args.no_sort)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(formatted)
        print(f"Formatted env written to {args.output}")
    else:
        sys.stdout.write(formatted)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envguard",
        description="EnvGuard: CLI tool to validate, audit, and sanitize .env files.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # check
    p_check = subparsers.add_parser("check", help="Audit .env file for security and hygiene issues")
    p_check.add_argument("file", help="Path to the .env file")
    p_check.add_argument("--json", action="store_true", help="Output results in JSON format")
    p_check.add_argument("--strict", action="store_true", help="Exit with 1 on warnings as well as errors")

    # diff
    p_diff = subparsers.add_parser("diff", help="Compare target .env against template (.env.example)")
    p_diff.add_argument("target", help="Path to the active .env file")
    p_diff.add_argument("--template", required=True, help="Path to template (.env.example)")
    p_diff.add_argument("--json", action="store_true", help="Output results in JSON format")

    # mask
    p_mask = subparsers.add_parser("mask", help="Mask secrets in .env for safe display or logging")
    p_mask.add_argument("file", help="Path to the .env file")
    p_mask.add_argument("--all", action="store_true", help="Mask all values, not only sensitive keys")
    p_mask.add_argument("-o", "--output", help="Output file path (prints to stdout if omitted)")

    # format
    p_fmt = subparsers.add_parser("format", help="Canonicalize and sort .env keys")
    p_fmt.add_argument("file", help="Path to the .env file")
    p_fmt.add_argument("--no-sort", action="store_true", help="Preserve existing line order")
    p_fmt.add_argument("-o", "--output", help="Output file path (prints to stdout if omitted)")

    return parser


def main(args_list: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(args_list)

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "check":
        return cmd_check(args)
    elif args.command == "diff":
        return cmd_diff(args)
    elif args.command == "mask":
        return cmd_mask(args)
    elif args.command == "format":
        return cmd_format(args)
    return 1
