#!/usr/bin/env python3
"""Autonomous Daily Demo Generator for daily-demo-lab.

Runs autonomously in GitHub Actions or locally.
Inspects existing projects, generates a new standalone demo for today,
runs automated tests, validates structure, and updates CATALOG.md.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
PROJECTS_DIR = ROOT / "projects"
CATALOG_PATH = ROOT / "CATALOG.md"
README_PATH = ROOT / "README.md"
CURRENT_INFO_PATH = ROOT / ".current_demo_info"


def get_dhaka_date() -> str:
    """Returns today's date in Asia/Dhaka (UTC+6) formatted as YYYY-MM-DD."""
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo("Asia/Dhaka")
        return datetime.datetime.now(tz).strftime("%Y-%m-%d")
    except Exception:
        tz = datetime.timezone(datetime.timedelta(hours=6))
        return datetime.datetime.now(tz).strftime("%Y-%m-%d")


def find_existing_demos() -> List[Path]:
    """Returns list of existing project directories."""
    if not PROJECTS_DIR.exists():
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        return []
    return sorted([p for p in PROJECTS_DIR.iterdir() if p.is_dir()])


def check_today_demo_exists(today_str: str) -> Optional[Path]:
    """Returns project path if today's demo already exists."""
    for demo in find_existing_demos():
        if demo.name.startswith(today_str):
            return demo
    return None


def run_cmd(cmd: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def build_fallback_demo(today_str: str, existing_names: List[str]) -> Dict[str, Any]:
    """Provides curated fallback demos in case Gemini API is unavailable."""
    candidates = [
        {
            "slug": "markdown-table-formatter",
            "name": "Markdown Table Formatter",
            "description": "CLI and library to parse, format, column-align, and sort Markdown tables.",
            "technology": "Python 3 (Standard Library)",
            "files": {
                "requirements.txt": "# Python standard library only\n",
                "run.py": (
                    "#!/usr/bin/env python3\n"
                    "import sys\n"
                    "from formatter.cli import main\n"
                    "if __name__ == '__main__':\n"
                    "    sys.exit(main())\n"
                ),
                "formatter/__init__.py": (
                    "from .table import MarkdownTable, format_table, align_table\n"
                    "__all__ = ['MarkdownTable', 'format_table', 'align_table']\n"
                ),
                "formatter/table.py": (
                    "from dataclasses import dataclass\n"
                    "from typing import List, Optional\n\n"
                    "@dataclass\n"
                    "class MarkdownTable:\n"
                    "    headers: List[str]\n"
                    "    rows: List[List[str]]\n"
                    "    alignments: List[str]  # 'left', 'right', 'center'\n\n"
                    "    def render(self) -> str:\n"
                    "        col_count = len(self.headers)\n"
                    "        widths = [len(h) for h in self.headers]\n"
                    "        for row in self.rows:\n"
                    "            for idx in range(col_count):\n"
                    "                val = row[idx] if idx < len(row) else ''\n"
                    "                widths[idx] = max(widths[idx], len(val))\n"
                    "        widths = [max(w, 3) for w in widths]\n\n"
                    "        def format_cell(text: str, width: int, align: str) -> str:\n"
                    "            if align == 'right':\n"
                    "                return text.rjust(width)\n"
                    "            elif align == 'center':\n"
                    "                return text.center(width)\n"
                    "            return text.ljust(width)\n\n"
                    "        lines = []\n"
                    "        header_line = '| ' + ' | '.join(format_cell(h, widths[i], self.alignments[i]) for i, h in enumerate(self.headers)) + ' |'\n"
                    "        lines.append(header_line)\n"
                    "        sep_cells = []\n"
                    "        for i, align in enumerate(self.alignments):\n"
                    "            w = widths[i]\n"
                    "            if align == 'right':\n"
                    "                sep_cells.append('-' * (w - 1) + ':')\n"
                    "            elif align == 'center':\n"
                    "                sep_cells.append(':' + '-' * (w - 2) + ':')\n"
                    "            else:\n"
                    "                sep_cells.append('-' * w)\n"
                    "        lines.append('| ' + ' | '.join(sep_cells) + ' |')\n"
                    "        for row in self.rows:\n"
                    "            cells = [format_cell(row[i] if i < len(row) else '', widths[i], self.alignments[i]) for i in range(col_count)]\n"
                    "            lines.append('| ' + ' | '.join(cells) + ' |')\n"
                    "        return '\\n'.join(lines)\n\n"
                    "def parse_table(markdown_text: str) -> MarkdownTable:\n"
                    "    lines = [l.strip() for l in markdown_text.strip().splitlines() if l.strip()]\n"
                    "    if len(lines) < 2:\n"
                    "        raise ValueError('Markdown table must have at least header and separator lines.')\n"
                    "    def split_row(line: str) -> List[str]:\n"
                    "        parts = [p.strip() for p in line.strip('|').split('|')]\n"
                    "        return parts\n"
                    "    headers = split_row(lines[0])\n"
                    "    sep_row = split_row(lines[1])\n"
                    "    alignments = []\n"
                    "    for s in sep_row:\n"
                    "        if s.startswith(':') and s.endswith(':'):\n"
                    "            alignments.append('center')\n"
                    "        elif s.endswith(':'):\n"
                    "            alignments.append('right')\n"
                    "        else:\n"
                    "            alignments.append('left')\n"
                    "    while len(alignments) < len(headers):\n"
                    "        alignments.append('left')\n"
                    "    rows = [split_row(l) for l in lines[2:]]\n"
                    "    return MarkdownTable(headers=headers, rows=rows, alignments=alignments)\n\n"
                    "def format_table(markdown_text: str) -> str:\n"
                    "    table = parse_table(markdown_text)\n"
                    "    return table.render()\n\n"
                    "def align_table(table: MarkdownTable, col_idx: int, align: str) -> MarkdownTable:\n"
                    "    if col_idx < len(table.alignments):\n"
                    "        table.alignments[col_idx] = align\n"
                    "    return table\n"
                ),
                "formatter/cli.py": (
                    "import argparse\n"
                    "import sys\n"
                    "from .table import format_table\n\n"
                    "SAMPLE = '''| Name | Role | Score |\\n|---|---|---|\\n| Alice | Lead | 95 |\\n| Bob | Developer | 88 |'''\n\n"
                    "def main(argv=None) -> int:\n"
                    "    parser = argparse.ArgumentParser(description='Format and pretty-print Markdown tables.')\n"
                    "    parser.add_argument('--demo', action='store_true', help='Run with built-in sample table')\n"
                    "    args = parser.parse_args(argv)\n"
                    "    if args.demo or not sys.stdin.isatty():\n"
                    "        content = SAMPLE if args.demo else sys.stdin.read()\n"
                    "        print(format_table(content))\n"
                    "        return 0\n"
                    "    parser.print_help()\n"
                    "    return 0\n"
                ),
                "tests/__init__.py": "",
                "tests/test_table.py": (
                    "import unittest\n"
                    "from formatter.table import parse_table, format_table, MarkdownTable\n\n"
                    "class TestMarkdownTable(unittest.TestCase):\n"
                    "    def test_parse_and_render(self):\n"
                    "        raw = '| Item | Price |\\n|---|---:|\\n| Coffee | 3.50 |\\n| Tea | 2.00 |'\n"
                    "        formatted = format_table(raw)\n"
                    "        self.assertIn('| Item   | Price |', formatted)\n"
                    "        self.assertIn('| Coffee |  3.50 |', formatted)\n\n"
                    "    def test_alignment_render(self):\n"
                    "        table = MarkdownTable(headers=['A', 'B'], rows=[['1', '2']], alignments=['left', 'right'])\n"
                    "        res = table.render()\n"
                    "        self.assertIn('---:', res)\n"
                    "if __name__ == '__main__':\n"
                    "    unittest.main()\n"
                ),
                "README.md": (
                    f"# Markdown Table Formatter\n\n"
                    f"A fast CLI utility and Python library to parse, column-align, pad, and format Markdown tables.\n\n"
                    f"## Features\n"
                    f"- Automatic column width calculation.\n"
                    f"- Respects and preserves left, right, and center alignments (`:---`, `---:`, `:---:`).\n"
                    f"- Zero external dependencies.\n\n"
                    f"## Usage\n"
                    f"```bash\n"
                    f"python run.py --demo\n"
                    f"```\n\n"
                    f"## Tests\n"
                    f"```bash\n"
                    f"python -m unittest discover -s tests -p 'test_*.py'\n"
                    f"```\n"
                ),
            },
        },
        {
            "slug": "json-schema-inferencer",
            "name": "JSON Schema Inferencer",
            "description": "Infers strict JSON Schema drafts from arbitrary JSON data payloads.",
            "technology": "Python 3 (Standard Library)",
            "files": {
                "requirements.txt": "# Standard library only\n",
                "run.py": (
                    "#!/usr/bin/env python3\n"
                    "import sys\n"
                    "from inferencer.cli import main\n"
                    "if __name__ == '__main__':\n"
                    "    sys.exit(main())\n"
                ),
                "inferencer/__init__.py": (
                    "from .schema import infer_schema\n"
                    "__all__ = ['infer_schema']\n"
                ),
                "inferencer/schema.py": (
                    "from typing import Any, Dict\n\n"
                    "def infer_type(val: Any) -> str:\n"
                    "    if val is None:\n"
                    "        return 'null'\n"
                    "    if isinstance(val, bool):\n"
                    "        return 'boolean'\n"
                    "    if isinstance(val, int):\n"
                    "        return 'integer'\n"
                    "    if isinstance(val, float):\n"
                    "        return 'number'\n"
                    "    if isinstance(val, str):\n"
                    "        return 'string'\n"
                    "    if isinstance(val, list):\n"
                    "        return 'array'\n"
                    "    if isinstance(val, dict):\n"
                    "        return 'object'\n"
                    "    return 'any'\n\n"
                    "def infer_schema(data: Any) -> Dict[str, Any]:\n"
                    "    t = infer_type(data)\n"
                    "    if t == 'object':\n"
                    "        props = {}\n"
                    "        required = []\n"
                    "        for k, v in data.items():\n"
                    "            props[k] = infer_schema(v)\n"
                    "            required.append(k)\n"
                    "        return {'type': 'object', 'properties': props, 'required': sorted(required)}\n"
                    "    elif t == 'array':\n"
                    "        if not data:\n"
                    "            return {'type': 'array', 'items': {}}\n"
                    "        return {'type': 'array', 'items': infer_schema(data[0])}\n"
                    "    return {'type': t}\n"
                ),
                "inferencer/cli.py": (
                    "import json\n"
                    "import sys\n"
                    "from .schema import infer_schema\n\n"
                    "def main(argv=None) -> int:\n"
                    "    sample = {'id': 101, 'name': 'Demo Device', 'active': True, 'tags': ['iot', 'sensor']}\n"
                    "    schema = infer_schema(sample)\n"
                    "    print(json.dumps(schema, indent=2))\n"
                    "    return 0\n"
                ),
                "tests/__init__.py": "",
                "tests/test_schema.py": (
                    "import unittest\n"
                    "from inferencer.schema import infer_schema\n\n"
                    "class TestSchema(unittest.TestCase):\n"
                    "    def test_primitive_inference(self):\n"
                    "        self.assertEqual(infer_schema(10)['type'], 'integer')\n"
                    "        self.assertEqual(infer_schema('test')['type'], 'string')\n"
                    "        self.assertEqual(infer_schema(True)['type'], 'boolean')\n\n"
                    "    def test_object_inference(self):\n"
                    "        s = infer_schema({'user': 'Alice', 'age': 30})\n"
                    "        self.assertEqual(s['type'], 'object')\n"
                    "        self.assertIn('user', s['properties'])\n"
                    "        self.assertEqual(s['required'], ['age', 'user'])\n"
                    "if __name__ == '__main__':\n"
                    "    unittest.main()\n"
                ),
                "README.md": (
                    f"# JSON Schema Inferencer\n\n"
                    f"Infers structural JSON schema definitions from raw data payloads.\n\n"
                    f"## Features\n"
                    f"- Generates typed schema definitions.\n"
                    f"- Recursive nested object and array item inspection.\n"
                    f"- Zero dependencies.\n\n"
                    f"## Usage\n"
                    f"```bash\n"
                    f"python run.py\n"
                    f"```\n\n"
                    f"## Tests\n"
                    f"```bash\n"
                    f"python -m unittest discover -s tests -p 'test_*.py'\n"
                    f"```\n"
                ),
            },
        },
    ]

    for c in candidates:
        folder_candidate = f"{today_str}-{c['slug']}"
        if folder_candidate not in existing_names and c["slug"] not in existing_names:
            return c

    # Default to candidate 0 with timestamp suffix if exhausted
    chosen = dict(candidates[0])
    chosen["slug"] = f"{chosen['slug']}-v2"
    return chosen


def call_gemini_api(api_key: str, prompt: str) -> Optional[str]:
    """Calls Gemini API using google.genai SDK or direct HTTPS request."""
    # Method 1: Try official google.genai SDK
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        if response and response.text:
            return response.text
    except Exception as e:
        print(f"DEBUG: google-genai SDK call notice: {e}. Trying REST endpoint...")

    # Method 2: Try REST HTTPS request via urllib
    try:
        import urllib.request
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4},
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            candidates = body.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
    except Exception as e:
        print(f"DEBUG: REST call failed: {e}")

    return None


def generate_with_gemini(today_str: str, existing_names: List[str], api_key: str) -> Optional[Dict[str, Any]]:
    """Prompts Gemini to generate a complete software project."""
    prompt = f"""
You are the autonomous lead software engineer for daily-demo-lab.
Today's date is: {today_str} (Asia/Dhaka).

Existing project folders (DO NOT DUPLICATE THESE IDEAS):
{json.dumps(existing_names, indent=2)}

Task:
Design and implement ONE small, useful, functional, distinct standalone software project.
Variety rotation: rotate among developer tools, CLI utilities, text processors, algorithms, financial/math calculators, games, or data tools.

Requirements:
1. Python 3 standard library only (zero external requirements).
2. Clean, tested, modular code.
3. Must include a project-specific README.md with Problem, Features, Setup, Usage, Tests.
4. Must include automated tests in tests/ using standard `unittest`.
5. Return ONLY a valid JSON object with this exact structure:
{{
  "slug": "short-kebab-name",
  "name": "Human Readable Project Name",
  "description": "One sentence summary of what this demo does.",
  "technology": "Python 3 (Standard Library)",
  "files": {{
     "README.md": "full markdown content...",
     "requirements.txt": "# Python standard library only\\n",
     "run.py": "#!/usr/bin/env python3\\n...",
     "package_name/__init__.py": "...",
     "package_name/core.py": "...",
     "package_name/cli.py": "...",
     "tests/__init__.py": "",
     "tests/test_core.py": "..."
  }}
}}
Do NOT wrap the JSON in conversational text. Only valid JSON.
"""
    raw_text = call_gemini_api(api_key, prompt)
    if not raw_text:
        return None

    # Clean markdown code fences if Gemini added ```json ... ```
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)

    try:
        return json.loads(cleaned.strip())
    except Exception as e:
        print(f"WARNING: Failed to parse Gemini JSON output: {e}")
        return None


def update_catalog_and_readme(today_str: str, project_dir_name: str, name: str, description: str, tech: str) -> None:
    """Appends project entry to CATALOG.md and root README.md."""
    # Update CATALOG.md
    catalog_line = f"| {today_str} | [{name}](projects/{project_dir_name}) | {description} | {tech} | Passing |\n"
    if CATALOG_PATH.exists():
        content = CATALOG_PATH.read_text(encoding="utf-8")
        if project_dir_name not in content:
            if not content.endswith("\n"):
                content += "\n"
            content += catalog_line
            CATALOG_PATH.write_text(content, encoding="utf-8")
            print(f"Updated CATALOG.md with {name}")

    # Update README.md
    if README_PATH.exists():
        readme_content = README_PATH.read_text(encoding="utf-8")
        if project_dir_name not in readme_content:
            # Replace placeholder row or insert into table
            placeholder = "| *(Demos will be listed chronologically here)* | | | |\n"
            new_row = f"| **{today_str}** | [{name}](projects/{project_dir_name}) | {tech} | Passing ✅ |\n"
            if placeholder in readme_content:
                readme_content = readme_content.replace(placeholder, new_row)
            else:
                # Append after the table header
                table_marker = "| :--- | :--- | :--- | :--- |\n"
                if table_marker in readme_content:
                    idx = readme_content.find(table_marker) + len(table_marker)
                    readme_content = readme_content[:idx] + new_row + readme_content[idx:]
            README_PATH.write_text(readme_content, encoding="utf-8")
            print(f"Updated README.md with {name}")


def main() -> int:
    today_str = get_dhaka_date()
    print(f"=== Daily Demo Lab Automation ===")
    print(f"Current Date (Asia/Dhaka): {today_str}")

    # Check if a project for today already exists
    existing_today = check_today_demo_exists(today_str)
    if existing_today:
        print(f"INFO: Project for today already exists: '{existing_today.name}'.")
        print("Running tests on existing project to verify integrity...")
        test_res = run_cmd([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], cwd=existing_today)
        print(test_res.stdout)
        if test_res.returncode != 0:
            print(f"ERROR: Existing project tests failed:\n{test_res.stderr}")
            return 1
        print("OK: Existing project is healthy and verified.")
        return 0

    existing_projects = [p.name for p in find_existing_demos()]
    print(f"Found {len(existing_projects)} existing demo projects.")

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    demo_spec: Optional[Dict[str, Any]] = None

    if api_key:
        print("GEMINI_API_KEY detected. Querying Gemini for a new demo idea...")
        demo_spec = generate_with_gemini(today_str, existing_projects, api_key)

    if not demo_spec:
        print("Using curated fallback demo generator...")
        demo_spec = build_fallback_demo(today_str, existing_projects)

    slug = demo_spec["slug"].lower().strip()
    # Ensure kebab-case
    slug = re.sub(r"[^a-z0-9\-]", "-", slug).strip("-")
    project_folder_name = f"{today_str}-{slug}"
    project_dir = PROJECTS_DIR / project_folder_name

    print(f"Creating project: {project_folder_name} ({demo_spec['name']})")
    project_dir.mkdir(parents=True, exist_ok=True)

    # Write project files
    for rel_path, file_content in demo_spec["files"].items():
        dest = project_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(file_content, encoding="utf-8")

    # Run tests on the generated project
    print("Running project test suite...")
    test_res = run_cmd([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], cwd=project_dir)
    print(test_res.stdout)
    if test_res.returncode != 0:
        print(f"ERROR: Project unit tests failed:\n{test_res.stderr}")
        return 1
    print("All project tests passed!")

    # Validate structure with scripts/validate_demo.py
    print("Validating project structure...")
    val_res = run_cmd([sys.executable, "scripts/validate_demo.py"])
    print(val_res.stdout)
    if val_res.returncode != 0:
        print(f"ERROR: Structure validation failed:\n{val_res.stderr}")
        return 1

    # Update CATALOG.md and README.md
    update_catalog_and_readme(
        today_str=today_str,
        project_dir_name=project_folder_name,
        name=demo_spec["name"],
        description=demo_spec["description"],
        tech=demo_spec.get("technology", "Python 3"),
    )

    # Write commit info file for GitHub Actions step
    CURRENT_INFO_PATH.write_text(f"{today_str} {demo_spec['name']}", encoding="utf-8")
    print(f"SUCCESS: Successfully created and validated demo '{project_folder_name}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
