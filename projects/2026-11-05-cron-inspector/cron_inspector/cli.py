"""Command line interface for cron-inspector."""
import argparse
import json
import sys
from datetime import datetime
from .parser import parse_cron, CronParseError
from .humanizer import humanize_cron
from .scheduler import get_next_runs


def _format_delta(td) -> str:
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if days > 0:
        return f"in {days} day{'s' if days != 1 else ''}, {hours:02d}:{minutes:02d}:{seconds:02d}"
    if hours > 0:
        return f"in {hours}h {minutes}m {seconds}s"
    return f"in {minutes}m {seconds}s"


def cmd_explain(args):
    try:
        expr = parse_cron(args.expression)
    except CronParseError as e:
        if args.json:
            print(json.dumps({"error": str(e), "valid": False}, indent=2))
        else:
            print(f"Syntax Error: {e}", file=sys.stderr)
        return 1

    description = humanize_cron(expr)
    now = datetime.now() if not args.reference_time else datetime.fromisoformat(args.reference_time)
    upcoming = get_next_runs(expr, base_time=now, count=args.count)

    if args.json:
        payload = {
            "expression": expr.raw,
            "valid": True,
            "explanation": description,
            "fields": expr.as_dict(),
            "next_runs": [dt.isoformat() for dt in upcoming]
        }
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Cron Expression: {expr.raw}")
    print(f"Explanation    : {description}")
    print("\nField Breakdown:")
    print(f"  Minute       : {expr.minute.raw:<10} -> {list(expr.minute.values)}")
    print(f"  Hour         : {expr.hour.raw:<10} -> {list(expr.hour.values)}")
    print(f"  Day of Month : {expr.day_of_month.raw:<10} -> {list(expr.day_of_month.values)}")
    print(f"  Month        : {expr.month.raw:<10} -> {list(expr.month.values)}")
    print(f"  Day of Week  : {expr.day_of_week.raw:<10} -> {list(expr.day_of_week.values)}")

    if upcoming:
        print(f"\nNext {len(upcoming)} Scheduled Runs (relative to {now.strftime('%Y-%m-%d %H:%M:%S')}):")
        for i, dt in enumerate(upcoming, 1):
            diff = dt - now
            print(f"  {i}. {dt.strftime('%Y-%m-%d %H:%M:%S')} ({_format_delta(diff)})")
    return 0


def cmd_validate(args):
    try:
        parse_cron(args.expression)
        if args.json:
            print(json.dumps({"expression": args.expression, "valid": True}, indent=2))
        else:
            print(f"VALID: '{args.expression}' is a valid 5-field cron expression.")
        return 0
    except CronParseError as e:
        if args.json:
            print(json.dumps({"expression": args.expression, "valid": False, "error": str(e)}, indent=2))
        else:
            print(f"INVALID: {e}", file=sys.stderr)
        return 1


def cmd_next(args):
    try:
        expr = parse_cron(args.expression)
    except CronParseError as e:
        if args.json:
            print(json.dumps({"error": str(e), "valid": False}, indent=2))
        else:
            print(f"Syntax Error: {e}", file=sys.stderr)
        return 1

    try:
        base_dt = datetime.fromisoformat(args.reference_time) if args.reference_time else datetime.now()
    except ValueError:
        print(f"Invalid ISO date/time format for --from: '{args.reference_time}'", file=sys.stderr)
        return 1

    runs = get_next_runs(expr, base_time=base_dt, count=args.count)

    if args.json:
        payload = {
            "expression": expr.raw,
            "from": base_dt.isoformat(),
            "count": len(runs),
            "next_runs": [dt.isoformat() for dt in runs]
        }
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Upcoming {len(runs)} execution times for '{expr.raw}':")
    for i, dt in enumerate(runs, 1):
        diff = dt - base_dt
        print(f"  {i}. {dt.strftime('%Y-%m-%d %H:%M:%S')} ({_format_delta(diff)})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cron-inspector",
        description="Inspect, humanize, validate, and forecast cron schedules."
    )
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # explain
    p_explain = subparsers.add_parser("explain", help="Explain and break down a cron schedule")
    p_explain.add_argument("expression", help="Standard 5-field cron expression, e.g., '*/15 9-17 * * 1-5'")
    p_explain.add_argument("--count", type=int, default=5, help="Number of upcoming runs to preview (default: 5)")
    p_explain.add_argument("--from", dest="reference_time", help="ISO reference datetime (default: now)")

    # validate
    p_val = subparsers.add_parser("validate", help="Check if a cron expression is valid")
    p_val.add_argument("expression", help="Cron expression to test")

    # next
    p_next = subparsers.add_parser("next", help="Calculate upcoming execution times")
    p_next.add_argument("expression", help="Cron expression")
    p_next.add_argument("--count", type=int, default=5, help="Number of runs to return (default: 5)")
    p_next.add_argument("--from", dest="reference_time", help="ISO reference datetime (default: now)")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "explain":
        return cmd_explain(args)
    elif args.command == "validate":
        return cmd_validate(args)
    elif args.command == "next":
        return cmd_next(args)
    return 0
