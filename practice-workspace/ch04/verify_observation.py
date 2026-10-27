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
    '_starter/frontend/app.js',
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
    """검사할 파일의 경로를 구하고 현재 Chapter 폴더 안의 경로인지 확인한다.

    상위 폴더나 외부를 가리키는 경로는 relative_to에서 예외로 거부한다.
    """
    path = ROOT / relative
    path.resolve().relative_to(ROOT)
    return path


def read_baseline() -> list[dict]:
    """제공 파일의 원래 크기·SHA-256 목록을 읽고 형식을 검사해 반환한다.

    SHA-256은 파일 내용의 변경 여부를 비교할 지문이다. 목록의 누락·중복이나
    잘못된 값이 있으면 ValueError를 발생시킨다. 기준 파일을 새로 만들지는 않는다.
    """
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
    """제공 파일을 기준 목록과 비교하고 변경·누락·읽기 실패를 보고한다.

    반환값은 일치 0, 파일 차이 1, 기준·읽기 문제로 검사하지 못한 경우 2다.
    업무 규칙의 동작은 실행하지 않으므로 이 검사만으로 승인 기능을 통과 판정하지 않는다.
    """
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
