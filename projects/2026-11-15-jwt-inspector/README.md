# JWT Inspector & Dev Mint

A zero-dependency developer utility to inspect, audit, verify, and generate JSON Web Tokens (JWT) using only the Python standard library.

## Problem

Developers frequently need to debug JWTs: checking expiry timestamps, reviewing claims, validating HMAC signatures, and diagnosing issues like `alg: none` vulnerabilities or malformed payloads. Existing web-based tools risk leaking sensitive tokens or production secrets to third parties, while heavy libraries introduce unnecessary dependencies for simple CLI tasks.

## Features

- **Deep Inspection**: Decodes and formats headers and payload claims with human-readable timestamps (`iat`, `exp`, `nbf`).
- **Signature Verification**: Verifies HMAC signatures (`HS256`, `HS384`, `HS512`) using standard library `hmac` and `hashlib`.
- **Security Audit**: Identifies critical vulnerabilities:
  - Unsecured tokens (`alg: none` or missing signature)
  - Expired tokens or tokens valid only in the future (`nbf`)
  - Missing `exp` expiration claim
  - Excessively long lifespans (> 30 days)
  - Weak secret detection against common dictionary passwords
- **Token Minting**: Quick CLI generation of test JWTs with custom claims, automatic `iat`, and custom expiry offsets.
- **CLI & Machine Readable**: Full terminal output with clear status flags, or `--json` for pipeline integration.
- **Pure Python**: 100% standard library; zero external dependencies.

## Setup

Requires Python 3.8+.

```bash
# No external installations needed
python3 run.py --help
```

## Usage

### 1. Inspect and Audit a Token

```bash
python3 run.py inspect "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMyIsIm5hbWUiOiJBbGljZSIsImV4cCI6MTk5OTk5OTk5OX0.sample_signature"
```

Or pipe via stdin:

```bash
echo "<token>" | python3 run.py inspect -
```

### 2. Verify Signature with Secret

```bash
python3 run.py inspect "<token>" --secret "my-secret-key"
```

### 3. Mint a Development JWT

```bash
python3 run.py create \
  --secret "my-secret-key" \
  --alg HS256 \
  --sub "user_42" \
  --claim role=admin \
  --claim email=user@example.com \
  --expires-in 3600
```

### 4. Machine-Readable Output

```bash
python3 run.py inspect "<token>" --json
```

## Tests

Run the test suite using `unittest`:

```bash
python3 -m unittest discover -s tests -v
```
