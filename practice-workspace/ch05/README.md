# Chapter 5 — 현재값·이력과 데이터 관계

두 실습은 같은 로컬 서버의 웹 화면에서 진행하며 DB는 각각 분리됩니다. Python 3.12 이상이 필요합니다.

## 시작

1. VS Code에서 ch05/를 열고 `powershell -NoProfile -ExecutionPolicy Bypass -File .\start_lab.ps1`로 실행합니다.
2. http://127.0.0.1:8305 를 엽니다. 포트가 사용 중이면 명령에 `-Port 8306`을 붙이고 주소도 바꿉니다. 종료는 Ctrl+C입니다.
3. 화면·DB 연결·SQL 추적은 제공됩니다. 업무 코드는 원고의 프롬프트로 AI와 구현합니다. 미구현 501은 실패를 숨기지 않는 시작본 안내입니다.

## 실습 1 — 입고·출고

원고 5.1 회의 뒤 5.2에서 backend/movement_rules.py와 backend/movement_write.py만 완성합니다.
초기화 후 A001 입고 10·출고 3을 입력해 현재고 7·이력 +10/-3·합계 7을 확인합니다.
재고 부족 거부·B001 입고 4도 확인하고 실제 실행 결과를 복사해 AI 검증에 전달합니다.
DB는 .lab/stock.sqlite3입니다. 실습 1 초기화는 이 실습의 두 품목 수량·이력만 지웁니다.

## 실습 2 — 상품 삭제와 취급 중단

실습 1을 마친 뒤 화면의 실습 2 링크 또는 http://127.0.0.1:8305/relationships 를 엽니다.
원고 5.4의 회의·프롬프트로 backend/relationship_write.py와 backend/relationship_read.py만 완성합니다.
상품코드 A001·상품명 샘플 상품·수량 5로 상품과 거래를 준비합니다. 거래번호는 T-0001입니다.
상품 삭제 시도는 실제 DB 외래 키로 거부돼야 합니다. 취급 중단 후 선택 목록은 0건이지만 예전 거래는 남아야 합니다.
관리할 상품에는 취급 중단 상품도 남으므로 새 거래용 선택 목록과 구분하세요.
DB는 .lab/relationships.sqlite3입니다. 준비는 기존 데이터를 덮어쓰지 않습니다. 다시 시작할 때만 실습 2 초기화를 누릅니다.
기존 PostgreSQL 세 구간 SQL은 선택 참고입니다. 기본 실습에서는 Supabase를 준비하지 않습니다.

## 실제 결과·검사·복구

SQL 상세는 실제 SQLite 실행 콜백·전달값·확정/취소·별도 연결 재조회를 보여 줍니다.
각 화면의 실행 결과 복사 버튼은 해당 탭에서 관찰한 내역만 복사합니다. 새로고침하면 탭 내역은 사라지고 DB는 보존됩니다.
`python` 대신 아래 가상환경 Python으로 실행하세요. 검사는 임시 사본·별도 서버·DB를 사용하며 사용 중인 데이터는 보존합니다.

```powershell
.\.venv\Scripts\python.exe .\verify_observation.py
.\.venv\Scripts\python.exe .\verify_web.py
.\.venv\Scripts\python.exe .\verify_relationships.py
```

verify_observation은 제공 기반, verify_web은 실습 1, verify_relationships는 실습 2 검사입니다. 아직 구현하지 않은 실습은 완성 검사를 통과하지 않습니다.
브라우저 동작과 AI 생성 과정은 별도로 확인합니다. 막혔을 때만 reference/web/README.md의 선택 비교·복구 절차를 사용하세요.
초기화와 서버 재시작은 업무 코드를 복구하지 않습니다. 기준 시작본은 _starter/backend/에 있습니다.
기존 SQL과 .archive/는 웹 실습의 시작 데이터로 실행하지 않습니다.
