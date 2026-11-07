import argparse
import sys
from .table import format_table

SAMPLE = '''| Name | Role | Score |\n|---|---|---|\n| Alice | Lead | 95 |\n| Bob | Developer | 88 |'''

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Format and pretty-print Markdown tables.')
    parser.add_argument('--demo', action='store_true', help='Run with built-in sample table')
    args = parser.parse_args(argv)
    if args.demo or not sys.stdin.isatty():
        content = SAMPLE if args.demo else sys.stdin.read()
        print(format_table(content))
        return 0
    parser.print_help()
    return 0
