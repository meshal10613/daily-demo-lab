# Daily Demo Lab 🧪

Welcome to the **Daily Demo Lab**! A public collection of small, functional, standalone software demonstrations created daily.

Each project in this repository explores a practical concept, developer utility, algorithm, interactive web application, or visualization — fully implemented with working code, comprehensive documentation, and automated tests.

---

## 📅 Catalog Overview

All projects are indexed in [**`CATALOG.md`**](CATALOG.md).

| Date | Project | Technology | Status |
| :--- | :--- | :--- | :--- |
| *(Demos will be listed chronologically here)* | | | |

---

## 📂 Repository Structure

```text
daily-demo-lab/
├── .github/
│   └── workflows/
│       └── validate.yml          # GitHub Actions CI workflow for pull requests and main pushes
├── projects/
│   └── YYYY-MM-DD-short-name/    # Self-contained project directory
│       ├── README.md             # Project documentation, architecture, and usage
│       ├── requirements.txt      # Project dependencies (kept minimal)
│       ├── tests/                # Automated test suite
│       └── ...                   # Application source files
├── scripts/
│   └── validate_demo.py          # Structural validator for projects
├── CATALOG.md                    # Chronological catalog of all demos
├── .gitignore                    # Standard repository ignore rules
└── README.md                     # Repository entry point
```

---

## 🚀 Running Validation Locally

To verify all projects follow the required structure and contain valid assets:

```bash
python scripts/validate_demo.py
# or on Windows with py launcher:
py scripts/validate_demo.py
```

---

## 🛠️ Design Principles

1. **Self-Contained**: Each project is an independent application or library.
2. **Real Functionality**: No placeholder mockups or fake stub files.
3. **Zero / Minimal Bloat**: Relies primarily on language standard libraries or lightweight dependencies.
4. **Tested**: Every demo includes test cases validating both edge cases and core happy paths.
5. **Clear Documentation**: Every demo contains its own `README.md` with usage instructions and technical explanation.
