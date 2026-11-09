# JSON Schema Inferrer & Validator

A lightweight, zero-dependency Python CLI and library that analyzes sample JSON payloads to automatically generate clean, structured Draft-07 JSON schemas. It detects semantic string formats, merges heterogeneous types across multiple records, computes required properties, and includes a built-in schema validator.

## Problem

Writing JSON Schema by hand for APIs, event buses, or data pipelines is tedious, repetitive, and error-prone. Existing tools are often heavy npm dependencies or complex web apps. Developers frequently need a quick, scriptable CLI tool to inspect real-world API responses or JSON lines data and produce an accurate schema contract instantly.

## Features

- **Zero External Dependencies**: Powered exclusively by Python 3 standard library.
- **Multi-Sample Merging**: Combine hundreds of JSON payloads or array records to accurately detect optional fields and union types.
- **Semantic String Format Detection**: Detects `email`, `uuid`, `date-time`, `date`, `ipv4`, and `uri`.
- **Type Union Resolution**: Handles nullable fields (`["string", "null"]`) and mixed types cleanly.
- **Required Field Calculation**: Automatically determines required properties based on sample presence frequencies.
- **Built-in Instance Validator**: Validates payloads against generated or supplied schemas.
- **Flexible CLI & Programmatic API**: Read from files or STDIN; format outputs neatly with customizable indentation.

## Setup

Ensure Python 3.9+ is installed. No third-party packages are required.

```bash
# Verify Python version
python3 --version

# Make the runner executable
chmod +x run.py
```

## Usage

### CLI Usage

#### 1. Infer schema from a JSON file or STDIN

```bash
# Infer from a file
./run.py infer sample.json

# Infer with a custom title and indent
./run.py infer sample.json --title "UserEvent" --indent 2

# Infer from piped STDIN
curl -s https://api.example.com/users/1 | ./run.py infer -

# Disable string format detection (pure string types only)
./run.py infer sample.json --no-format
```

#### 2. Validate a JSON document against a schema

```bash
./run.py validate --schema schema.json --input instance.json
```

### Python API Usage

```python
from schema_infer import infer_schema, validate_instance

samples = [
    {"id": "123e4567-e89b-12d3-a456-426614174000", "email": "user@example.com", "age": 30},
    {"id": "223e4567-e89b-12d3-a456-426614174001", "email": "admin@domain.org", "age": None}
]

schema = infer_schema(samples, title="UserProfile")

# Test a payload
valid, errors = validate_instance({"id": "abc", "email": "not-an-email"}, schema)
print(f"Valid: {valid}, Errors: {errors}")
```

## Tests

Run the test suite using `unittest`:

```bash
python3 -m unittest discover -s tests
```
