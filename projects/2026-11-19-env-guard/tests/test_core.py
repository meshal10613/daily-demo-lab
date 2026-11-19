"""Unit tests for EnvGuard core functionality and CLI."""
import io
import json
import sys
import unittest
from envguard.core import (
    EnvParser,
    EnvAuditor,
    EnvComparator,
    EnvMasker,
    EnvFormatter,
)
from envguard.cli import main


class TestEnvParser(unittest.TestCase):
    def test_basic_parse(self):
        content = """
        # Configuration
        PORT=8080
        HOST=localhost
        export DEBUG=true
        """
        entries = EnvParser.parse(content)
        self.assertIn("PORT", entries)
        self.assertEqual(entries["PORT"].value, "8080")
        self.assertEqual(entries["HOST"].value, "localhost")
        self.assertTrue(entries["DEBUG"].is_export)
        self.assertEqual(entries["DEBUG"].value, "true")

    def test_quotes_and_comments(self):
        content = """
        SECRET_PHRASE="hello world" # an inline comment
        SINGLE_QUOTED='foo bar'
        UNQUOTED=some_val # comment here
        """
        entries = EnvParser.parse(content)
        self.assertEqual(entries["SECRET_PHRASE"].value, "hello world")
        self.assertEqual(entries["SECRET_PHRASE"].comment, "an inline comment")
        self.assertEqual(entries["SINGLE_QUOTED"].value, "foo bar")
        self.assertEqual(entries["UNQUOTED"].value, "some_val")
        self.assertEqual(entries["UNQUOTED"].comment, "comment here")


class TestEnvAuditor(unittest.TestCase):
    def test_audit_detects_placeholders_and_empty(self):
        content = """
        API_KEY=changeme
        DATABASE_URL=http://insecure-db.internal
        APP_SECRET=short
        EMPTY_VAR=
        """
        entries = EnvParser.parse(content)
        issues = EnvAuditor.audit(entries)

        issue_map = {i.key: i for i in issues}
        self.assertIn("API_KEY", issue_map)
        self.assertEqual(issue_map["API_KEY"].severity, "ERROR")
        self.assertIn("Placeholder", issue_map["API_KEY"].message)

        self.assertIn("DATABASE_URL", issue_map)
        self.assertEqual(issue_map["DATABASE_URL"].severity, "WARNING")
        self.assertIn("Insecure HTTP", issue_map["DATABASE_URL"].message)

        self.assertIn("APP_SECRET", issue_map)
        self.assertEqual(issue_map["APP_SECRET"].severity, "WARNING")

        self.assertIn("EMPTY_VAR", issue_map)
        self.assertEqual(issue_map["EMPTY_VAR"].severity, "WARNING")

    def test_audit_clean_env(self):
        content = """
        DATABASE_URL=https://secure-db.internal
        JWT_SECRET=super_secret_high_entropy_token_1234567890
        """
        entries = EnvParser.parse(content)
        issues = EnvAuditor.audit(entries)
        self.assertEqual(len(issues), 0)


class TestEnvComparator(unittest.TestCase):
    def test_diff_missing_and_extra_keys(self):
        template_content = """
        APP_NAME=MyApp
        PORT=3000
        DATABASE_URL=postgres://localhost:5432/db
        """
        target_content = """
        APP_NAME=MyApp
        NEW_SETTING=1
        DATABASE_URL=postgres://localhost:5432/db
        """
        template = EnvParser.parse(template_content)
        target = EnvParser.parse(target_content)

        diff = EnvComparator.diff(target, template)
        self.assertIn("PORT", diff.missing_in_target)
        self.assertIn("NEW_SETTING", diff.extra_in_target)
        self.assertEqual(diff.identical_to_template, [("APP_NAME", "MyApp"), ("DATABASE_URL", "postgres://localhost:5432/db")])


class TestEnvMaskerAndFormatter(unittest.TestCase):
    def test_masker(self):
        content = """
        API_SECRET=supersecretvalue
        PUBLIC_PORT=8080
        """
        entries = EnvParser.parse(content)
        masked = EnvMasker.mask_all(entries)
        self.assertEqual(masked["PUBLIC_PORT"], "8080")
        self.assertTrue(masked["API_SECRET"].startswith("su"))
        self.assertTrue(masked["API_SECRET"].endswith("ue"))
        self.assertIn("****", masked["API_SECRET"])

    def test_formatter(self):
        content = """
        Z_KEY=val
        A_KEY=hello world
        export B_KEY=123 # some flag
        """
        entries = EnvParser.parse(content)
        formatted = EnvFormatter.format_entries(entries, sort_keys=True)
        lines = formatted.strip().split("\n")
        self.assertEqual(lines[0], 'A_KEY="hello world"')
        self.assertEqual(lines[1], "export B_KEY=123 # some flag")
        self.assertEqual(lines[2], "Z_KEY=val")


class TestCliIntegration(unittest.TestCase):
    def test_cli_check_json(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            f.write("SECRET_KEY=changeme\n")
            f.flush()
            filename = f.name

        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            exit_code = main(["check", filename, "--json"])
            output = sys.stdout.getvalue()
            data = json.loads(output)
            self.assertEqual(exit_code, 1)
            self.assertEqual(len(data["issues"]), 1)
            self.assertEqual(data["issues"][0]["key"], "SECRET_KEY")
        finally:
            sys.stdout = old_stdout


if __name__ == "__main__":
    unittest.main()
