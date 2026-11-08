"""Command Line Interface for CIDR Network Planner."""

import argparse
import json
import sys
from typing import List, Optional
from .core import inspect_cidr, split_cidr, contains_target, audit_cidrs


def format_inspect_table(data: dict) -> str:
    """Format inspection details into an aligned terminal view."""
    lines = [
        "=" * 50,
        f" CIDR Block: {data['cidr']} (IPv{data['version']})",
        "=" * 50,
        f" Network Address   : {data['network_address']}",
        f" Netmask           : {data['netmask']}",
        f" Wildcard Mask     : {data['wildcard_mask']}",
        f" Broadcast Address : {data['broadcast_address']}",
        f" Prefix Length     : /{data['prefix_length']}",
        f" Total Addresses   : {data['total_addresses']:,}",
        f" Usable Hosts     : {data['usable_addresses']:,}",
        f" Usable Host Range : {data['first_usable']} -> {data['last_usable']}",
        f" Classification    : {data['classification']}",
        "-" * 50,
        f" Binary Network    : {data['binary']['network_binary']}",
        f" Binary Netmask    : {data['binary']['netmask_binary']}",
        "=" * 50,
    ]
    return "\n".join(lines)


def format_split_table(subnets: List[dict]) -> str:
    """Format subnet split list into a readable table."""
    lines = [
        f"Generated {len(subnets)} subnets:",
        "-" * 78,
        f"{'#':<4} {'Subnet CIDR':<20} {'Usable Range':<38} {'Hosts':>8}",
        "-" * 78,
    ]
    for s in subnets:
        rng = f"{s['first_usable']} - {s['last_usable']}"
        lines.append(f"{s['index']:<4} {s['cidr']:<20} {rng:<38} {s['usable_addresses']:>8,}")
    lines.append("-" * 78)
    return "\n".join(lines)


def format_audit_report(report: dict) -> str:
    """Format audit results into terminal output."""
    lines = [
        "=" * 60,
        f" CIDR Audit Report: {report['total_inputs']} networks analyzed",
        "=" * 60,
    ]
    if report["errors"]:
        lines.append("\n[!] Syntax Errors Detected:")
        for err in report["errors"]:
            lines.append(f"  - '{err['input']}': {err['error']}")

    if not report["has_overlaps"]:
        lines.append("\n[+] Result: No collisions or overlaps found. Topology is clean!")
    else:
        lines.append(f"\n[!] Warning: Found {report['overlap_count']} collisions / overlaps:")
        for ov in report["overlaps"]:
            lines.append(f"  * {ov['cidr_a']} <-> {ov['cidr_b']} ({ov['relationship']})")

    lines.append("=" * 60)
    return "\n".join(lines)


def main(args: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cidr-planner",
        description="CIDR inspection, subnet partitioning, and network overlap auditing tool.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # Inspect command
    p_inspect = subparsers.add_parser("inspect", help="Inspect a CIDR block")
    p_inspect.add_argument("cidr", help="CIDR to inspect (e.g. 192.168.1.0/24 or 2001:db8::/64)")
    p_inspect.add_argument("--json", action="store_true", help="Output as JSON")

    # Split command
    p_split = subparsers.add_parser("split", help="Split a CIDR block into smaller subnets")
    p_split.add_argument("cidr", help="Parent CIDR to split (e.g. 10.0.0.0/16)")
    group = p_split.add_mutually_exclusive_group(required=True)
    group.add_argument("--prefix", type=int, help="Target subnet prefix length (e.g. 24)")
    group.add_argument("--count", type=int, help="Number of subnets to create (e.g. 4)")
    p_split.add_argument("--json", action="store_true", help="Output as JSON")

    # Contains command
    p_contains = subparsers.add_parser("contains", help="Check if target IP or subnet is within parent CIDR")
    p_contains.add_argument("parent", help="Parent CIDR network (e.g. 10.0.0.0/8)")
    p_contains.add_argument("target", help="Target IP address or CIDR network (e.g. 10.1.2.3 or 10.1.0.0/16)")
    p_contains.add_argument("--json", action="store_true", help="Output as JSON")

    # Audit command
    p_audit = subparsers.add_parser("audit", help="Audit multiple CIDRs for overlaps and collisions")
    p_audit.add_argument(
        "cidrs",
        nargs="+",
        help="List of CIDRs to check, or '-' to read from standard input",
    )
    p_audit.add_argument("--json", action="store_true", help="Output as JSON")

    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        return 1

    try:
        if parsed.command == "inspect":
            res = inspect_cidr(parsed.cidr)
            if parsed.json:
                print(json.dumps(res, indent=2))
            else:
                print(format_inspect_table(res))
            return 0

        elif parsed.command == "split":
            res = split_cidr(parsed.cidr, new_prefix=parsed.prefix, count=parsed.count)
            if parsed.json:
                print(json.dumps(res, indent=2))
            else:
                print(format_split_table(res))
            return 0

        elif parsed.command == "contains":
            res = contains_target(parsed.parent, parsed.target)
            if parsed.json:
                print(json.dumps(res, indent=2))
            else:
                symbol = "✓" if res["is_contained"] else "✗"
                status = "CONTAINS" if res["is_contained"] else "DOES NOT CONTAIN"
                print(f"{symbol} {res['parent_cidr']} {status} {res['target_type']} '{res['target']}'")
            return 0 if res["is_contained"] else 2

        elif parsed.command == "audit":
            raw_items = []
            if len(parsed.cidrs) == 1 and parsed.cidrs[0] == "-":
                raw_items = [line.strip() for line in sys.stdin if line.strip()]
            else:
                raw_items = parsed.cidrs

            res = audit_cidrs(raw_items)
            if parsed.json:
                print(json.dumps(res, indent=2))
            else:
                print(format_audit_report(res))
            return 1 if res["has_overlaps"] else 0

    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1

    return 0
