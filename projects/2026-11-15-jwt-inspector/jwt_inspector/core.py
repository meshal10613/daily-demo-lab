"""Core JWT decoding, verification, and minting engine."""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

SUPPORTED_HMAC_ALGORITHMS = {
    "HS256": hashlib.sha256,
    "HS384": hashlib.sha384,
    "HS512": hashlib.sha512,
}

COMMON_WEAK_SECRETS = {
    "secret", "secret123", "password", "123456", "admin",
    "jwtsecret", "mysecret", "key", "test", "development"
}


def b64url_decode(payload: str) -> bytes:
    """Decode URL-safe base64 string with automatic padding."""
    payload = payload.strip()
    padding = 4 - (len(payload) % 4)
    if padding != 4:
        payload += "=" * padding
    return base64.urlsafe_b64decode(payload.encode("ascii"))


def b64url_encode(data: bytes) -> str:
    """Encode bytes into URL-safe base64 string without trailing padding."""
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


class TokenReport:
    """Structured representation of inspected token."""

    def __init__(
        self,
        raw_token: str,
        header: Dict[str, Any],
        payload: Dict[str, Any],
        signature: str,
        is_valid_format: bool = True,
        signature_verified: Optional[bool] = None,
        signature_error: Optional[str] = None,
        warnings: Optional[List[str]] = None,
    ):
        self.raw_token = raw_token
        self.header = header
        self.payload = payload
        self.signature = signature
        self.is_valid_format = is_valid_format
        self.signature_verified = signature_verified
        self.signature_error = signature_error
        self.warnings = warnings or []

    @property
    def algorithm(self) -> str:
        return str(self.header.get("alg", ""))

    @property
    def token_type(self) -> str:
        return str(self.header.get("typ", "JWT"))

    def to_dict(self) -> Dict[str, Any]:
        """Convert report into JSON-serializable dictionary."""
        now_ts = int(time.time())
        exp = self.payload.get("exp")
        nbf = self.payload.get("nbf")
        iat = self.payload.get("iat")

        time_meta = {}
        if isinstance(exp, (int, float)):
            time_meta["exp_iso"] = datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()
            time_meta["is_expired"] = now_ts > exp
            time_meta["expires_in_seconds"] = int(exp - now_ts)
        if isinstance(iat, (int, float)):
            time_meta["iat_iso"] = datetime.fromtimestamp(iat, tz=timezone.utc).isoformat()
        if isinstance(nbf, (int, float)):
            time_meta["nbf_iso"] = datetime.fromtimestamp(nbf, tz=timezone.utc).isoformat()
            time_meta["is_future"] = now_ts < nbf

        return {
            "valid_format": self.is_valid_format,
            "header": self.header,
            "payload": self.payload,
            "signature": self.signature,
            "signature_verified": self.signature_verified,
            "signature_error": self.signature_error,
            "timestamps": time_meta,
            "warnings": self.warnings,
        }


def decode_token(
    token: str,
    secret: Optional[str] = None,
    now_timestamp: Optional[int] = None,
) -> TokenReport:
    """Decode and audit a JWT string."""
    token = token.strip()
    parts = token.split(".")

    if len(parts) not in (2, 3):
        raise ValueError(
            f"Invalid JWT format: Expected 2 or 3 dot-separated segments, got {len(parts)}"
        )

    header_b64, payload_b64 = parts[0], parts[1]
    sig_b64 = parts[2] if len(parts) == 3 else ""

    # Decode Header
    try:
        header_json = b64url_decode(header_b64).decode("utf-8")
        header = json.loads(header_json)
        if not isinstance(header, dict):
            raise ValueError("Header is not a JSON object")
    except Exception as exc:
        raise ValueError(f"Malformed JWT header: {exc}") from exc

    # Decode Payload
    try:
        payload_json = b64url_decode(payload_b64).decode("utf-8")
        payload = json.loads(payload_json)
        if not isinstance(payload, dict):
            raise ValueError("Payload is not a JSON object")
    except Exception as exc:
        raise ValueError(f"Malformed JWT payload: {exc}") from exc

    now = int(time.time()) if now_timestamp is None else now_timestamp
    warnings: List[str] = []

    # Audit Algorithm & Signature
    alg = header.get("alg", "").upper()
    if not alg:
        warnings.append("Missing 'alg' in header.")
    elif alg == "NONE":
        warnings.append("Critical: Algorithm is set to 'none' (unsigned insecure token).")
    elif len(parts) == 2 or not sig_b64:
        warnings.append("Token is missing signature component.")

    # Audit Timestamps
    exp = payload.get("exp")
    iat = payload.get("iat")
    nbf = payload.get("nbf")

    if exp is None:
        warnings.append("Claim 'exp' is missing: token will never expire.")
    elif isinstance(exp, (int, float)):
        if exp < now:
            diff = now - int(exp)
            warnings.append(f"Token expired {diff} seconds ago.")
        elif iat and isinstance(iat, (int, float)):
            lifetime = exp - iat
            if lifetime > 30 * 86400:
                days = round(lifetime / 86400, 1)
                warnings.append(f"Excessively long token lifespan: {days} days.")
    else:
        warnings.append("Claim 'exp' must be a numeric Unix timestamp.")

    if nbf is not None and isinstance(nbf, (int, float)):
        if now < nbf:
            diff = int(nbf) - now
            warnings.append(f"Token not valid yet (nbf active in {diff} seconds).")

    # Signature Verification
    sig_verified: Optional[bool] = None
    sig_err: Optional[str] = None

    if secret is not None:
        if alg not in SUPPORTED_HMAC_ALGORITHMS:
            sig_err = f"Signature verification for '{alg}' requires external crypto (supported in stdlib: HS256, HS384, HS512)"
        else:
            sig_verified = verify_token_hmac(token, secret, alg)
            if not sig_verified:
                sig_err = "Signature mismatch using provided secret"

    # Weak secret heuristic check
    if secret and secret.lower() in COMMON_WEAK_SECRETS:
        warnings.append(f"Weak secret detected: '{secret}' is a common dictionary word.")

    return TokenReport(
        raw_token=token,
        header=header,
        payload=payload,
        signature=sig_b64,
        is_valid_format=True,
        signature_verified=sig_verified,
        signature_error=sig_err,
        warnings=warnings,
    )


def verify_token_hmac(token: str, secret: str, algorithm: str) -> bool:
    """Verify HMAC signature for a token string."""
    parts = token.strip().split(".")
    if len(parts) != 3:
        return False

    signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
    target_signature = parts[2]

    hash_func = SUPPORTED_HMAC_ALGORITHMS.get(algorithm.upper())
    if not hash_func:
        return False

    expected_digest = hmac.new(secret.encode("utf-8"), signing_input, hash_func).digest()
    expected_signature = b64url_encode(expected_digest)

    return hmac.compare_digest(target_signature, expected_signature)


def verify_token(token: str, secret: str) -> Tuple[bool, Optional[str]]:
    """Convenience validator returning (is_valid, error_message)."""
    try:
        report = decode_token(token, secret=secret)
        if report.signature_verified is False:
            return False, report.signature_error or "Invalid signature"
        if any("expired" in w.lower() for w in report.warnings):
            return False, "Token is expired"
        return True, None
    except Exception as exc:
        return False, str(exc)


def create_token(
    payload: Dict[str, Any],
    secret: Optional[str] = None,
    algorithm: str = "HS256",
    headers: Optional[Dict[str, Any]] = None,
    expires_in_seconds: Optional[int] = None,
) -> str:
    """Mint a new JWT with optional HMAC signature."""
    alg = algorithm.upper()
    token_header = {"typ": "JWT", "alg": alg}
    if headers:
        token_header.update(headers)

    token_payload = dict(payload)
    now = int(time.time())

    if "iat" not in token_payload:
        token_payload["iat"] = now

    if expires_in_seconds is not None and "exp" not in token_payload:
        token_payload["exp"] = now + int(expires_in_seconds)

    header_b64 = b64url_encode(json.dumps(token_header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = b64url_encode(json.dumps(token_payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}"

    if alg == "NONE" or secret is None:
        return f"{signing_input}."

    hash_func = SUPPORTED_HMAC_ALGORITHMS.get(alg)
    if not hash_func:
        raise ValueError(
            f"Unsupported algorithm '{alg}'. Stdlib supports: {list(SUPPORTED_HMAC_ALGORITHMS.keys())}"
        )

    signature_bytes = hmac.new(
        secret.encode("utf-8"), signing_input.encode("ascii"), hash_func
    ).digest()
    signature_b64 = b64url_encode(signature_bytes)

    return f"{signing_input}.{signature_b64}"
