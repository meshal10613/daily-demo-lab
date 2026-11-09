"""CLI execution and argument tests."""
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from schema_infer.cli import main


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_infer_file_output(self):
        sample_path = os.path.join(self.temp_dir.name, "sample.json")
        output_path = os.path.join(self.temp_dir.name, "schema.json")
        sample_data = [{"user_id": 1, "name": "Alex"}, {"user_id": 2, "name": "Beth"}]
        with open(sample_path, "w", encoding="utf-8") as f:
            json.dump(sample_data, f)

        exit_code = main(["infer", sample_path, "-o", output_path, "--title", "Users"])
        self.assertEqual(exit_code, 0)
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        self.assertEqual(schema["title"], "Users")
        self.assertEqual(schema["type"], "object")
        self.assertIn("user_id", schema["properties"])

    def test_validate_success(self):
        schema_path = os.path.join(self.temp_dir.name, "schema.json")
        input_path = os.path.join(self.temp_dir.name, "instance.json")
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump({"type": "object", "required": ["token"]}, f)
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump({"token": "secret"}, f)

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = main(["validate", "-s", schema_path, "-i", input_path])
            self.assertEqual(exit_code, 0)
            self.assertIn("SUCCESS", fake_out.getvalue())

    def test_validate_failure(self):
        schema_path = os.path.join(self.temp_dir.name, "schema.json")
        input_path = os.path.join(self.temp_dir.name, "instance.json")
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump({"type": "object", "required": ["token"]}, f)
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump({"wrong_key": 123}, f)

        with patch("sys.stderr", new=io.StringIO()) as fake_err:
            exit_code = main(["validate", "-s", schema_path, "-i", input_path])
            self.assertEqual(exit_code, 2)
            self.assertIn("FAILURE", fake_err.getvalue())


if __name__ == "__main__":
    unittest.main()
