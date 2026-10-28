# Chapter 5 — 현재값·이력과 데이터 관계

실습 1은 웹에서 입력·조회합니다. 실습 2는 기존 Supabase SQL 방식이며 웹 DB와 분리돼 있습니다.

## 실습 1: 입고·출고를 입력하고 실제 SQL을 확인합니다

1. VS Code에서 ch05/를 엽니다. Python 3.12 이상과 첫 설치 시 인터넷이 필요합니다.
2. `powershell -NoProfile -ExecutionPolicy Bypass -File .\start_lab.ps1`로 실행하고 http://127.0.0.1:8305 를 엽니다.
   포트가 사용 중이면 `-Port 8306`을 붙이고 같은 주소로 접속합니다. 종료는 Ctrl+C입니다.
3. 원고 5.1의 회의 뒤 5.2의 프롬프트로 두 업무 파일을 구현합니다. 시작본은 미구현 501로 안내하며 가짜 데이터를 보여 주지 않습니다.
4. 초기화 뒤 A001에 입고 10, 출고 3을 입력합니다. 현재고 7, 이력 +10/-3, 합계 7과 실제 SQL 상세를 확인합니다.
5. 재고 부족 거부와 다른 품목·수량도 확인합니다. 실행 내역 복사 버튼으로 실제 결과를 AI 검증에 전달하고 화면으로 보고합니다.

| 역할 | 파일 |
|---|---|
| AI가 구현할 업무 판단 | backend/movement_rules.py |
| AI가 구현할 현재고·이력 저장 | backend/movement_write.py |
| 제공 HTTP·트랜잭션·SQLite 실행 추적·재조회 | backend/app.py, backend/store.py, backend/contracts.py |
| 제공 관찰 화면 | frontend/index.html, frontend/app.js, frontend/style.css |
| 제공 검사·복구 기준 | verify_observation.py, verify_web.py, web-baseline.json, _starter/ |

DB는 .lab/stock.sqlite3이며 서버 재시작 후에도 보존됩니다. 초기화는 두 품목 현재고·이력만 되돌리고 코드는 유지합니다.
현재 수량·이력은 별도 연결로 다시 읽습니다. SQL은 실제 SQLite 콜백 결과이며 BEGIN/COMMIT/ROLLBACK과 재조회 단계가 구분됩니다.
검증용 내역은 이 브라우저 탭의 메모리에만 쌓이며 새로고침하면 지워집니다. 필요한 때 실행 결과 복사 버튼을 사용하세요.

구현 뒤 `.\.venv\Scripts\python.exe .\verify_web.py`로 임시 사본에서 API·저장·취소·실행 추적을 확인합니다.
`.\.venv\Scripts\python.exe .\verify_observation.py`는 제공 기반의 변경만 확인합니다. UI 검사는 실제 브라우저에서 따로 합니다.
막혔을 때만 reference/web/README.md의 선택 비교 절차를 사용합니다. 참고 결과를 생성 코드의 성공으로 대신 보고하지 않습니다.

## 실습 2: Supabase SQL 세 구간

실습 1을 마친 뒤 원고 5.4의 회의를 읽고 sql/02_relationship_and_delete.sql만 조사·생성합니다.
기초 실습 전용 Supabase에서 구간 1 준비 → 구간 2 삭제 시도 → 구간 3 목록 제외 순서로 실행·조회합니다.
각 구간은 독립된 BEGIN·검사·COMMIT입니다. 구간 1만 초기화하며 구간 2·3의 직전 상태 검사·재시작 규칙은 sql/README.md를 따릅니다.
실행 상태와 조회 결과를 그대로 복사합니다. 별도 표는 만들지 않고 0행은 '0행'으로 남겨도 됩니다.
생성·검증에서 reference/를 답안으로 읽지 않습니다. 막혔을 때만 reference/README.md로 비교합니다.

기존 sql/01_current_and_history.sql 방식과 reference/01_current_and_history.sql은 PostgreSQL 선택 참고 자료입니다.
웹 실습 1의 시작 데이터로 실행하지 않습니다. .archive/와 예전 초기화·리셋 SQL도 사용하지 않습니다.
