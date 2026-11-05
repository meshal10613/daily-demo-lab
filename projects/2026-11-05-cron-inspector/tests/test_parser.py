"""Unit tests for cron expression parser and humanizer."""
import unittest
from cron_inspector.parser import parse_cron, CronParseError
from cron_inspector.humanizer import humanize_cron


class TestCronParser(unittest.TestCase):
    def test_standard_wildcards(self):
        expr = parse_cron("* * * * *")
        self.assertEqual(len(expr.minute.values), 60)
        self.assertEqual(len(expr.hour.values), 24)
        self.assertEqual(len(expr.day_of_month.values), 31)
        self.assertEqual(len(expr.month.values), 12)
        self.assertEqual(len(expr.day_of_week.values), 7)
        self.assertEqual(humanize_cron(expr), "Every minute")

    def test_step_values(self):
        expr = parse_cron("*/15 */6 * * *")
        self.assertEqual(expr.minute.values, (0, 15, 30, 45))
        self.assertEqual(expr.hour.values, (0, 6, 12, 18))

    def test_ranges_and_lists(self):
        expr = parse_cron("5,10 1-3 1,15 * 1-5")
        self.assertEqual(expr.minute.values, (5, 10))
        self.assertEqual(expr.hour.values, (1, 2, 3))
        self.assertEqual(expr.day_of_month.values, (1, 15))
        self.assertEqual(expr.day_of_week.values, (1, 2, 3, 4, 5))

    def test_text_month_and_day_names(self):
        expr = parse_cron("0 12 1 JAN,JUN MON-FRI")
        self.assertEqual(expr.month.values, (1, 6))
        self.assertEqual(expr.day_of_week.values, (1, 2, 3, 4, 5))

    def test_sunday_normalization(self):
        # 0 and 7 are Sunday in cron standards
        expr1 = parse_cron("0 0 * * 0")
        expr2 = parse_cron("0 0 * * 7")
        expr3 = parse_cron("0 0 * * SUN")
        self.assertEqual(expr1.day_of_week.values, (0,))
        self.assertEqual(expr2.day_of_week.values, (0,))
        self.assertEqual(expr3.day_of_week.values, (0,))

    def test_invalid_field_count(self):
        with self.assertRaises(CronParseError):
            parse_cron("* * * *")
        with self.assertRaises(CronParseError):
            parse_cron("* * * * * *")

    def test_out_of_bounds(self):
        with self.assertRaises(CronParseError):
            parse_cron("60 * * * *")
        with self.assertRaises(CronParseError):
            parse_cron("* 24 * * *")
        with self.assertRaises(CronParseError):
            parse_cron("* * 0 * *")
        with self.assertRaises(CronParseError):
            parse_cron("* * * 13 *")
        with self.assertRaises(CronParseError):
            parse_cron("* * * * 8")

    def test_reversed_range(self):
        with self.assertRaises(CronParseError):
            parse_cron("30-10 * * * *")

    def test_humanizer_phrases(self):
        self.assertEqual(
            humanize_cron(parse_cron("30 4 * * 1-5")),
            "At 04:30, Monday through Friday"
        )
        self.assertEqual(
            humanize_cron(parse_cron("0 0 1 1 *")),
            "At 00:00, on the 1st of the month, in January"
        )
        self.assertEqual(
            humanize_cron(parse_cron("*/10 9-17 * * *")),
            "Every 10 minutes, between 09:00 and 17:59"
        )
