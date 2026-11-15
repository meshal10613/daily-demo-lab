"""Unit tests for jwt-inspector core and CLI."""

import json
import time
import unittest
from jwt_inspector.core import (
    decode_token,
    create_token,
    verify_token,
    b64url_encode,
    b64url_decode,
)
from jwt_inspector.cli import main, parse_custom_claims


class TestBase64Url(unittest.TestCase):
    def test_round_trip(self):
        raw = b"Hello world, this is a test string with symbols +/=!"
        encoded = b64url_encode(raw)
        self.assertNotIn("=", encoded)
        self.assertNotIn("+", encoded)
        self.assertNotIn("/", encoded)
        decoded = b64url_decode(encoded)
        self.assertEqual(raw, decoded)


class TestTokenOperations(unittest.TestCase):
    def setUp(self):
        self.secret = "correct-horse-battery-staple-xyz123"
        self.claims = {"sub": "usr_100", "role": "developer", "admin": True}

    def test_create_and_decode_valid_hs256(self):
        token = create_token(self.claims, secret=self.secret, algorithm="HS256", expires_in_seconds=600)
        report = decode_token(token, secret=self.secret)

        self.assertEqual(report.header.get("alg"), "HS256")
        self.assertEqual(report.payload.get("sub"), "usr_100")
        self.assertEqual(report.payload.get("role"), "developer")
        self.assertEqual(report.payload.get("admin"), True)
        self.assertTrue(report.signature_verified)
        self.assertIsNone(report.signature_error)

    def test_algorithms_hs384_hs512(self):
        for alg in ["HS384", "HS512"]:
            token = create_token(self.claims, secret=self.secret, algorithm=alg)
            report = decode_token(token, secret=self.secret)
            self.assertEqual(report.header.get("alg"), alg)
            self.assertTrue(report.signature_verified)

    def test_signature_verification_failure(self):
        token = create_token(self.claims, secret=self.secret, algorithm="HS256")
        report = decode_token(token, secret="wrong-secret-value")
        self.assertFalse(report.signature_verified)
        self.assertIn("mismatch", report.signature_error.lower())

    def test_expired_token_detection(self):
        now = int(time.time())
        expired_payload = {"sub": "expired_user", "iat": now - 200, "exp": now - 100}
        token = create_token(expired_payload, secret=self.secret)

        report = decode_token(token, secret=self.secret, now_timestamp=now)
        self.assertTrue(any("expired" in w.lower() for w in report.warnings))

        is_valid, err = verify_token(token, self.secret)
        self.assertFalse(is_valid)
        self.assertIn("expired", err.lower())

    def test_not_before_detection(self):
        now = 1700000000
        future_payload = {"sub": "future_user", "iat": now, "nbf": now + 300, "exp": now + 3600}
        token = create_token(future_payload, secret=self.secret)
        report = decode_token(token, now_timestamp=now)
        self.assertTrue(any("not valid yet" in w.lower() for w in report.warnings))

    def test_missing_exp_warning(self):
        token = create_token({"sub": "eternal_user"}, secret=self.secret, expires_in_seconds=None)
        report = decode_token(token)
        self.assertTrue(any("will never expire" in w.lower() for w in report.warnings))

    def test_alg_none_warning(self):
        token = create_token({"sub": "insecure_user"}, algorithm="none")
        report = decode_token(token)
        self.assertEqual(report.algorithm.upper(), "NONE")
        self.assertTrue(any("unsigned insecure" in w.lower() for w in report.warnings))

    def test_weak_secret_audit(self):
        token = create_token(self.claims, secret="password")
        report = decode_token(token, secret="password")
        self.assertTrue(any("weak secret" in w.lower() for w in report.warnings))

    def test_malformed_token_formats(self):
        with self.assertRaises(ValueError):
            decode_token("not-a-token")
        with self.assertRaises(ValueError):
            decode_token("one.two.three.four")
        with self.assertRaises(ValueError):
            decode_token("notbase64!.notbase64!.sig")


class TestCli(unittest.TestCase):
    def test_claim_parser(self):
        claims = parse_custom_claims(["foo=bar", "count=42", "active=true", "rate=3.14"])
        self.assertEqual(claims["foo"], "bar")
        self.assertEqual(claims["count"], 42)
        self.assertEqual(claims["active"], True)
        self.assertAlmostEqual(claims["rate"], 3.14)

    def test_cli_create_and_inspect_json(self):
        import io
        from unittest.mock import patch

        # Create token via CLI
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            ret = main([
                "create",
                "--secret", "testsecret123",
                "--sub", "cli_user",
                "--claim", "role=tester",
                "--expires-in", "600",
            ])
            self.assertEqual(ret, 0)
            created_token = mock_stdout.getvalue().strip()

        # Inspect token via CLI JSON
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            ret = main([
                "inspect",
                created_token,
                "--secret", "testsecret123",
                "--json",
            ])
            self.assertEqual(ret, 0)
            out_json = json.loads(mock_stdout.getvalue())
            self.assertTrue(out_json["valid_format"])
            self.assertTrue(out_json["signature_verified"])
            self.assertEqual(out_json["payload"]["sub"], "cli_user")
            self.assertEqual(out_json["payload"]["role"], "tester")


if __name__ == "__main__":
    unittest.main()
