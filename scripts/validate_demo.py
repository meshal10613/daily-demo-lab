from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"

def main():
    if not PROJECTS.exists():
        print("ERROR: projects/ directory is missing")
        return 1

    demos = sorted(p for p in PROJECTS.iterdir() if p.is_dir())

    if not demos:
        print("ERROR: no demo projects found")
        return 1

    for demo in demos:
        if not (demo / "README.md").is_file():
            print(f"ERROR: {demo.name} has no README.md")
            return 1

        source_files = [
            p for p in demo.rglob("*")
            if p.is_file()
            and p.name != "README.md"
            and ".git" not in p.parts
        ]

        if not source_files:
            print(f"ERROR: {demo.name} contains no project files")
            return 1

        print(f"OK: {demo.name} ({len(source_files)} files)")

    print(f"Validated {len(demos)} demo projects.")
    return 0

if __name__ == "__main__":
    sys.exit(main())