"""제공 관찰 도구가 배포 기준과 같은지 확인한다. 업무 파일은 대상에서 제외한다."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parent
baseline = json.loads((root / "observation-baseline.json").read_text(encoding="utf-8"))
failed = []
for name, expected in baseline.items():
    path = root / name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        failed.append(name)
for name in failed:
    print("FAIL    provided observation file: " + name)
print("FAIL: restore the provided observation tools" if failed else "PASS: provided observation tools")
sys.exit(1 if failed else 0)
