"""Unit tests for JSON schema inference and validation."""
import unittest
from schema_infer.core import infer_schema, validate_instance, get_json_type
from schema_infer.detector import detect_string_format


class TestDetector(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(detect_string_format("2026-11-09T08:30:00Z"), "date-time")
        self.assertEqual(detect_string_format("2026-11-09"), "date")
        self.assertEqual(detect_string_format("user@test.org"), "email")
        self.assertEqual(detect_string_format("123e4567-e89b-12d3-a456-426614174000"), "uuid")
        self.assertEqual(detect_string_format("192.168.1.1"), "ipv4")
        self.assertEqual(detect_string_format("https://example.com/api"), "uri")
        self.assertIsNone(detect_string_format("hello world"))


class TestSchemaInferrer(unittest.TestCase):
    def test_primitive_types(self):
        self.assertEqual(get_json_type(42), "integer")
        self.assertEqual(get_json_type(3.14), "number")
        self.assertEqual(get_json_type("test"), "string")
        self.assertEqual(get_json_type(True), "boolean")
        self.assertEqual(get_json_type(None), "null")
        self.assertEqual(get_json_type([]), "array")
        self.assertEqual(get_json_type({}), "object")

    def test_simple_object_inference(self):
        data = {
            "id": 101,
            "name": "Alice",
            "active": True,
            "balance": 49.95
        }
        schema = infer_schema(data, title="Account")
        self.assertEqual(schema["type"], "object")
        self.assertEqual(schema["title"], "Account")
        props = schema["properties"]
        self.assertEqual(props["id"]["type"], "integer")
        self.assertEqual(props["name"]["type"], "string")
        self.assertEqual(props["active"]["type"], "boolean")
        self.assertEqual(props["balance"]["type"], "number")
        self.assertEqual(sorted(schema["required"]), ["active", "balance", "id", "name"])

    def test_multiple_samples_merging(self):
        samples = [
            {"id": "123e4567-e89b-12d3-a456-426614174000", "email": "a@b.com", "notes": "first"},
            {"id": "223e4567-e89b-12d3-a456-426614174001", "email": "c@d.com", "notes": None},
            {"id": "323e4567-e89b-12d3-a456-426614174002", "email": "e@f.com"}
        ]
        schema = infer_schema(samples)
        props = schema["properties"]
        # notes is present in 2 out of 3, so not required
        self.assertEqual(schema["required"], ["email", "id"])
        # notes is string or null
        self.assertEqual(props["notes"]["type"], ["null", "string"])
        # format detection
        self.assertEqual(props["id"]["format"], "uuid")
        self.assertEqual(props["email"]["format"], "email")

    def test_nested_arrays_and_objects(self):
        sample = {
            "org": "Engineering",
            "members": [
                {"name": "Alice", "role": "Lead"},
                {"name": "Bob", "role": "Dev"}
            ]
        }
        schema = infer_schema(sample)
        self.assertEqual(schema["type"], "object")
        self.assertEqual(schema["properties"]["members"]["type"], "array")
        item_props = schema["properties"]["members"]["items"]["properties"]
        self.assertIn("name", item_props)
        self.assertIn("role", item_props)


class TestValidator(unittest.TestCase):
    def test_valid_instance(self):
        schema = {
            "type": "object",
            "properties": {
                "age": {"type": "integer"},
                "email": {"type": "string", "format": "email"}
            },
            "required": ["age"]
        }
        valid, errors = validate_instance({"age": 25, "email": "hi@example.com"}, schema)
        self.assertTrue(valid)
        self.assertEqual(errors, [])

    def test_invalid_instance(self):
        schema = {
            "type": "object",
            "properties": {
                "age": {"type": "integer"},
                "email": {"type": "string", "format": "email"}
            },
            "required": ["age", "email"]
        }
        # missing age, bad email
        valid, errors = validate_instance({"email": "not-email"}, schema)
        self.assertFalse(valid)
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("Missing required property 'age'" in e for e in errors))
        self.assertTrue(any("does not match format 'email'" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
