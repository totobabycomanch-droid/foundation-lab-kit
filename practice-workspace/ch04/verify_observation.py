"""Check the supplied observation files without reading outside this chapter."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / "observation-baseline.json"
FIXED_PATHS = (
    '.gitignore',
    'AGENTS.md',
    'README.md',
    'start_lab.ps1',
    'requirements.txt',
    'package.json',
    'package-lock.json',
    'verify_observation.py',
    'verify_business_rules.py',
    'backend/__init__.py',
    'backend/app.py',
    'backend/lab_auth.py',
    'backend/store.py',
    'frontend/index.html',
    'frontend/app.js',
    'frontend/transport.js',
    'frontend/style.css',
    '_starter/backend/approval_rules.py',
    '_starter/frontend/approval-action.js',
    'lessons/01_requirement.md',
    'lessons/02_role.md',
    'lessons/03_state.md',
    'lessons/04_company.md',
    'backend/defect_rules.py',
    'backend/defect_approval.py',
    '_starter/backend/defect_scope.py',
)


def chapter_path(relative: str) -> Path:
    path = ROOT / relative
    path.resolve().relative_to(ROOT)
    return path


def read_baseline() -> list[dict]:
    BASELINE.resolve().relative_to(ROOT)
    document = json.loads(BASELINE.read_text(encoding="utf-8-sig"))
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise ValueError("unsupported baseline")
    entries = document.get("fixed_files")
    if not isinstance(entries, list) or len(entries) != len(FIXED_PATHS):
        raise ValueError("incomplete baseline")
    names = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("path") not in FIXED_PATHS:
            raise ValueError("unexpected baseline path")
        if not isinstance(entry.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
            raise ValueError("invalid hash")
        if type(entry.get("bytes")) is not int or entry["bytes"] < 0:
            raise ValueError("invalid file size")
        names.append(entry["path"])
    if set(names) != set(FIXED_PATHS):
        raise ValueError("duplicate or missing baseline path")
    return entries


def main() -> int:
    try:
        entries = read_baseline()
    except (OSError, ValueError, TypeError):
        print("NOT RUN observation baseline is missing, unreadable or invalid.")
        print("Use the original chapter package; do not regenerate the baseline.")
        return 2
    differences = []
    unreadable = []
    for entry in entries:
        name = entry["path"]
        try:
            content = chapter_path(name).read_bytes()
        except FileNotFoundError:
            differences.append(f"missing: {name}")
            continue
        except (OSError, ValueError):
            unreadable.append(name)
            continue
        if len(content) != entry["bytes"] or hashlib.sha256(content).hexdigest() != entry["sha256"]:
            differences.append(f"modified: {name}")
    for difference in differences:
        print(f"FAIL {difference}")
    for name in unreadable:
        print(f"NOT RUN cannot read chapter file: {name}")
    if differences or unreadable:
        print("Do not edit observation files or their baseline to make this check pass.")
        return 1 if differences else 2
    print(f"PASS observation files match the supplied baseline ({len(entries)} files).")
    print("INFO business-rule behavior is not tested; continue with the chapter's screen checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
