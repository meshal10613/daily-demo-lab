# EnvGuard

EnvGuard is a zero-dependency CLI tool and library for validating, auditing, formatting, and synchronizing `.env` configuration files against templates (e.g., `.env.example`).

## Problem

Environment variable files are a frequent source of deployment failures and security leaks:
- Developers add new variables to `.env` but forget to update `.env.example`.
- Production deployments break because expected keys are missing.
- Accidental commits leak production secrets or leave default placeholder credentials like `password123` or `TODO`.
- Inconsistent spacing, quoting, and formatting make diffing `.env` files noisy.

## Features

- **Robust `.env` Parser**: Handles quotes (`'single'`, `"double"`), comments, `export` prefixes, empty lines, and escaped characters.
- **Template Diffing (`diff`)**: Compare target `.env` files against `.env.example` to detect missing keys, extra undocumented keys, and unchanged placeholder values.
- **Security & Hygiene Audit (`check`)**: Flags empty values, weak default placeholders (`changeme`, `admin`, `secret`), unmasked high-entropy tokens, and insecure protocol URLs (`http://`).
- **Safe Redaction (`mask`)**: Generates sanitized `.env` exports with secrets masked (e.g., `sk-***89ab`) suitable for debugging or sharing logs.
- **Normalization & Sorting (`format`)**: Cleans whitespace, removes trailing comments, and sorts keys alphabetically.
- **CI/CD Ready**: Supports JSON output and strict exit codes (`0` for clean, `1` for errors/violations).

## Setup

EnvGuard requires Python 3.8+ with no external dependencies.

```bash
# Make the entry point executable
chmod +x run.py
```

## Usage

### 1. Audit an environment file

```bash
./run.py check .env
```

Check with JSON output for CI pipelines:
```bash
./run.py check .env --json --strict
```

### 2. Compare against a template (`.env.example`)

```bash
./run.py diff .env --template .env.example
```

### 3. Mask sensitive credentials

```bash
./run.py mask .env
```

### 4. Canonicalize and sort keys

```bash
./run.py format .env --output .env.cleaned
```

## Running Tests

Run the test suite using standard `unittest`:

```bash
python3 -m unittest discover -s tests
```
