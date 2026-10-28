"""Check provided web foundation, not business-rule correctness."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
FIXED = ('start_lab.ps1', 'requirements.txt', '.gitignore', 'backend/__init__.py',
         'backend/contracts.py', 'backend/app.py', 'backend/store.py',
         'frontend/index.html', 'frontend/app.js', 'frontend/style.css',
         '_starter/backend/movement_rules.py', '_starter/backend/movement_write.py',
         'verify_observation.py', 'verify_web.py')


def main():
    expected = json.loads((ROOT/'web-baseline.json').read_text(encoding='utf-8'))
    assert set(expected) == set(FIXED), 'Provided baseline inventory changed'
    changed = [n for n in FIXED if not (ROOT/n).is_file()
               or hashlib.sha256((ROOT/n).read_bytes()).hexdigest() != expected[n]]
    for name in changed:
        print('FAIL provided file changed:', name)
    if changed:
        return 1
    print('PASS provided web foundation unchanged; business rules and screen behavior require separate checks')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
