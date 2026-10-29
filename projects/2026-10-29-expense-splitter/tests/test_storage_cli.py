"""Unit tests for storage serialization and CLI commands."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from decimal import Decimal
from expense_splitter.calculator import ExpenseGroup
from expense_splitter.cli import main, build_sample_trip
from expense_splitter.storage import (
    group_to_dict,
    load_group_from_dict,
    save_group_to_file,
    load_group_from_file,
)


class TestStorageAndCLI(unittest.TestCase):

    def test_json_roundtrip(self):
        original = build_sample_trip()
        data = group_to_dict(original)
        restored = load_group_from_dict(data)

        self.assertEqual(restored.name, original.name)
        self.assertEqual(restored.participants, original.participants)
        self.assertEqual(len(restored.expenses), len(original.expenses))
        self.assertEqual(restored.get_total_spending(), original.get_total_spending())

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file = Path(tmpdir) / "test_group.json"
            save_group_to_file(original, tmp_file)
            from_file = load_group_from_file(tmp_file)
            self.assertEqual(from_file.get_total_spending(), original.get_total_spending())

    def test_cli_demo(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["demo"])
        self.assertEqual(ret, 0)
        output = f.getvalue()
        self.assertIn("MOUNTAIN CABIN WEEKEND TRIP", output)
        self.assertIn("Optimal Debt Settlement Plan", output)

    def test_cli_quick_split(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["quick-split", "--total", "90.00", "--payer", "Alice", "--people", "Alice", "Bob", "Charlie"])
        self.assertEqual(ret, 0)
        output = f.getvalue()
        self.assertIn("QUICK SPLIT", output)
        self.assertIn("Bob pays Alice -> $30.00", output)
        self.assertIn("Charlie pays Alice -> $30.00", output)

    def test_cli_file_json(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tf:
            trip = build_sample_trip()
            save_group_to_file(trip, tf.name)
            tf_path = tf.name

        try:
            f = io.StringIO()
            with redirect_stdout(f):
                ret = main(["file", tf_path, "--json"])
            self.assertEqual(ret, 0)
            parsed = json.loads(f.getvalue())
            self.assertIn("group", parsed)
            self.assertIn("settlements", parsed)
            self.assertIn("balances", parsed)
        finally:
            Path(tf_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
