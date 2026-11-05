"""Unit tests for future occurrence scheduler and CLI integration."""
import unittest
from datetime import datetime
from cron_inspector.parser import parse_cron
from cron_inspector.scheduler import get_next_runs
from cron_inspector.cli import main
from io import StringIO
import sys
import json


class TestCronScheduler(unittest.TestCase):
    def test_every_minute(self):
        expr = parse_cron("* * * * *")
        base = datetime(2026, 11, 5, 10, 30, 15)
        runs = get_next_runs(expr, base_time=base, count=3)
        expected = [
            datetime(2026, 11, 5, 10, 31, 0),
            datetime(2026, 11, 5, 10, 32, 0),
            datetime(2026, 11, 5, 10, 33, 0),
        ]
        self.assertEqual(runs, expected)

    def test_step_hour_and_minute(self):
        expr = parse_cron("0 9-17/2 * * *")  # Hours: 9, 11, 13, 15, 17 at minute 0
        base = datetime(2026, 11, 5, 12, 0, 0)
        runs = get_next_runs(expr, base_time=base, count=4)
        expected = [
            datetime(2026, 11, 5, 13, 0, 0),
            datetime(2026, 11, 5, 15, 0, 0),
            datetime(2026, 11, 5, 17, 0, 0),
            datetime(2026, 11, 6, 9, 0, 0),
        ]
        self.assertEqual(runs, expected)

    def test_monthly_day(self):
        expr = parse_cron("0 0 15 * *")
        base = datetime(2026, 11, 5, 0, 0, 0)
        runs = get_next_runs(expr, base_time=base, count=3)
        expected = [
            datetime(2026, 11, 15, 0, 0, 0),
            datetime(2026, 12, 15, 0, 0, 0),
            datetime(2027, 1, 15, 0, 0, 0),
        ]
        self.assertEqual(runs, expected)

    def test_leap_year_and_february_handling(self):
        # 2028 is a leap year; 2026 and 2027 are not
        expr = parse_cron("0 0 29 2 *")
        base = datetime(2026, 1, 1, 0, 0, 0)
        runs = get_next_runs(expr, base_time=base, count=1)
        self.assertEqual(runs, [datetime(2028, 2, 29, 0, 0, 0)])

    def test_dow_matching(self):
        # 2026-11-05 is a Thursday (Cron DOW = 4)
        # Request Fridays only (DOW = 5)
        expr = parse_cron("0 18 * * 5")
        base = datetime(2026, 11, 5, 10, 0, 0)
        runs = get_next_runs(expr, base_time=base, count=2)
        expected = [
            datetime(2026, 11, 6, 18, 0, 0),
            datetime(2026, 11, 13, 18, 0, 0),
        ]
        self.assertEqual(runs, expected)


class TestCLI(unittest.TestCase):
    def test_cli_validate_valid(self):
        code = main(["validate", "*/5 * * * *"])
        self.assertEqual(code, 0)

    def test_cli_validate_invalid(self):
        code = main(["validate", "99 * * * *"])
        self.assertEqual(code, 1)

    def test_cli_explain_json(self):
        buf = StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            code = main(["--json", "explain", "30 2 * * 1-5", "--from", "2026-11-05T00:00:00", "--count", "2"])
            self.assertEqual(code, 0)
            output = buf.getvalue()
            data = json.loads(output)
            self.assertTrue(data["valid"])
            self.assertEqual(data["expression"], "30 2 * * 1-5")
            self.assertEqual(len(data["next_runs"]), 2)
        finally:
            sys.stdout = old_stdout

    def test_cli_next_command(self):
        buf = StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            code = main(["next", "0 12 * * *", "--count", "3", "--from", "2026-11-05T10:00:00"])
            self.assertEqual(code, 0)
            output = buf.getvalue()
            self.assertIn("2026-11-05 12:00:00", output)
            self.assertIn("2026-11-06 12:00:00", output)
            self.assertIn("2026-11-07 12:00:00", output)
        finally:
            sys.stdout = old_stdout
