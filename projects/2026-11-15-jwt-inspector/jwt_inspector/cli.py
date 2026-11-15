"""Command line interface for JWT inspector."""

import argparse
import json
import sys
from typing import List, Optional
from .core import decode_token, create_token, SUPPORTED_HMAC_ALGORITHMS


def parse_custom_claims(claims_list: Optional[List[str]]) -> dict:
    """Parse key=value claim arguments into a dictionary with basic type inference."""
    claims = {}
    if not claims_list:
        return claims

    for item in claims_list:
        if "=" not in item:
            raise ValueError(f"Claim must be in key=value format, got '{item}'")
        key, val = item.split("=", 1)
        key = key.strip()
        val = val.strip()

        # Type inference
        if val.lower() == "true":
            claims[key] = True
        elif val.lower() == "false":
            claims[key] = False
        elif val.isdigit():
            claims[key] = int(val)
        else:
            try:
                claims[key] = float(val)
            except ValueError:
                claims[key] = val
    return claims


def format_text_report(report) -> str:
    """Format token report for human-readable terminal display."""
    data = report.to_dict()
    lines = []
    lines.append("=" * 60)
    lines.append(" JWT INSPECTION REPORT")
    lines.append("=" * 60)

    # Header
    lines.append("\n[Header]")
    lines.append(json.dumps(data["header"], indent=2))

    # Payload
    lines.append("\n[Payload / Claims]")
    lines.append(json.dumps(data["payload"], indent=2))

    # Timing Info
    if data["timestamps"]:
        lines.append("\n[Timestamp Analysis]")
        for k, v in data["timestamps"].items():
            lines.append(f"  {k:20}: {v}")

    # Signature Verification
    lines.append("\n[Signature]")
    lines.append(f"  Algorithm: {report.algorithm or 'None'}")
    if report.signature:
        sig_preview = report.signature[:16] + "..." if len(report.signature) > 20 else report.signature
        lines.append(f"  Token Signature: {sig_preview}")
    else:
        lines.append("  Token Signature: (empty)")

    if report.signature_verified is not None:
        status = "VALID (PASS)" if report.signature_verified else "INVALID (FAIL)"
        lines.append(f"  Verification:    {status}")
    elif report.signature_error:
        lines.append(f"  Verification:    SKIPPED ({report.signature_error})")
    else:
        lines.append("  Verification:    SKIPPED (no --secret provided)")

    # Warnings / Audits
    lines.append("\n[Security Audit]")
    if not data["warnings"]:
        lines.append("  No warnings detected. Clean configuration.")
    else:
        for warn in data["warnings"]:
            lines.append(f"  [!] {warn}")

    lines.append("=" * 60)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Construct command line parser."""
    parser = argparse.ArgumentParser(
        prog="jwt-inspector",
        description="Inspect, audit, verify, and mint JSON Web Tokens.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Inspect Subcommand
    inspect_parser = subparsers.add_parser("inspect", help="Decode and inspect a JWT.")
    inspect_parser.add_argument(
        "token",
        help="JWT string or '-' to read token from standard input.",
    )
    inspect_parser.add_argument(
        "-s", "--secret",
        help="HMAC secret key to verify signature.",
        default=None,
    )
    inspect_parser.add_argument(
        "--json",
        action="store_true",
        help="Output analysis in JSON format.",
    )

    # Create / Mint Subcommand
    create_parser = subparsers.add_parser("create", help="Mint a new JWT for testing.")
    create_parser.add_argument(
        "-s", "--secret",
        help="HMAC secret key for signing. If omitted, generates unsigned token.",
        default=None,
    )
    create_parser.add_argument(
        "--alg",
        default="HS256",
        choices=list(SUPPORTED_HMAC_ALGORITHMS.keys()) + ["none"],
        help="Signature algorithm (default: HS256).",
    )
    create_parser.add_argument(
        "--sub",
        help="Subject claim ('sub').",
        default=None,
    )
    create_parser.add_argument(
        "--iss",
        help="Issuer claim ('iss').",
        default=None,
    )
    create_parser.add_argument(
        "--aud",
        help="Audience claim ('aud').",
        default=None,
    )
    create_parser.add_argument(
        "-e", "--expires-in",
        type=int,
        help="Token validity duration in seconds (sets 'exp' claim).",
        default=3600,
    )
    create_parser.add_argument(
        "-c", "--claim",
        action="append",
        help="Custom claim in key=val format (can be specified multiple times).",
    )

    return parser


def main(args=None) -> int:
    """Main CLI entrypoint."""
    parser = build_parser()
    parsed = parser.parse_args(args)

    try:
        if parsed.subcommand == "inspect":
            raw_token = parsed.token
            if raw_token == "-":
                raw_token = sys.stdin.read().strip()

            report = decode_token(raw_token, secret=parsed.secret)

            if parsed.json:
                print(json.dumps(report.to_dict(), indent=2))
            else:
                print(format_text_report(report))
            return 0

        elif parsed.subcommand == "create":
            payload = parse_custom_claims(parsed.claim)
            if parsed.sub:
                payload["sub"] = parsed.sub
            if parsed.iss:
                payload["iss"] = parsed.iss
            if parsed.aud:
                payload["aud"] = parsed.aud

            token = create_token(
                payload=payload,
                secret=parsed.secret,
                algorithm=parsed.alg,
                expires_in_seconds=parsed.expires_in,
            )
            print(token)
            return 0

    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1

    return 0
