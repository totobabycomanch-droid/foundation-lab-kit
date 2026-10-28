"""제공 기반의 변경만 검사한다. 업무 규칙과 화면은 별도로 확인한다."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parent
FIXED=('web_server.py','lab_store.py','lab_contracts.py','start_lab.ps1','frontend/index.html','frontend/app.js','frontend/style.css',
       '_starter/transaction_example.py','_starter/sale_example.py','_starter/test_examples.py','verify_observation.py','verify_web.py')


def main():
    expected=json.loads((ROOT/'observation-baseline.json').read_text(encoding='utf-8'))
    assert set(expected)==set(FIXED),'Provided file inventory changed'
    changed=[n for n in FIXED if not (ROOT/n).is_file() or hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=expected[n]]
    for n in changed:print('FAIL provided file changed:',n)
    if changed:return 1
    print('PASS provided observation foundation unchanged; business rules and UI require separate checks')
    return 0


if __name__=='__main__':raise SystemExit(main())
