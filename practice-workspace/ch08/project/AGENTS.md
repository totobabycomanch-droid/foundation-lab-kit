# Chapter 8 project 규칙

<!-- common-rules-version: chapter8-v2 -->

## 작업 시작 전 (approval-required)

- `../AGENTS.md`와 `../README.md`, 이 파일을 먼저 읽는다.
- 요구사항, 기존 파일, 변경 범위와 검증 방법을 먼저 보고하고 독자의 승인 뒤에만 변경한다.
- 승인된 현재 단계의 파일만 최소 변경하고 이전 단계 결과와 시작 파일을 보존한다.

## 보안과 검증 근거 (secrets-protected, evidence-scoped)

- `.env`, 비밀번호, API key, JWT와 실제 DB URL을 읽거나 출력하지 않는다.
- 결과는 `Pass`, `Fail`, `Not Run`, `테스트 없음`으로 구분하고 코드 검토인지 명령 실행인지 밝힌다.
- 실행하지 않은 테스트를 통과로 추정하지 않는다.
- 검증 요청의 보고는 확인할 질문·판정·근거의 표로 한다. 근거는 명령을 실행했으면 `실행:`,
  파일만 읽었으면 `코드 검토:`로 시작한다. `Fail`·`Not Run`·`테스트 없음` 항목은 표 아래에
  원인과 다음 확인 방법을 쓰고, 독자가 직접 확인할 최소 코드 한 곳을 지정한다.
- Mock 결과를 실제 SQL 실행·DB 저장·롤백·HTTP 요청의 성공 근거로 사용하지 않는다.

## 구현 책임

- 요청 해석과 업무 판단은 `services/`에 두고 DB에 접근하지 않는다.
- 저장은 `repositories/`에 두고, 재고·예치금·주문 저장을 한 트랜잭션으로 처리한다.
- HTTP 연결은 `routers/`에 두고 현재 값 조회, 호출 순서, 오류 코드의 HTTP 변환만 맡는다.
- 주문 가능 여부의 판단 규칙은 `services/`에만 둔다. 저장소의 조건부 갱신은 저장 시점에
  조건이 바뀌었는지 확인하는 최종 방어선이며 업무 판단을 대신하지 않는다.
- `.env.example`의 변수 이름만 참고한다.
- 변경 뒤 현재 단계의 확인 명령을 실행한다.


## 교육용 파일 위치와 공개 연결 규약

아래 경로는 project/ 기준이며 원고의 import·실행 명령을 연결하는 규약이다.
먼저 기존 파일을 조사하고 현재 단계의 파일만 생성·수정한다. 아직 없는 파일은
시작 키트의 결함이 아니며 후속 단계의 완성 코드를 미리 만들지 않는다.

| 단계 | 파일 | 공개 규약과 역할 |
|---|---|---|
| 8.2 요청 해석 | `services/franchise_order.py` | `FranchiseOrderEvent`(값을 바꿀 수 없는 요청 객체: `franchise_id`, `prod_code`, `qty`), `parse_franchise_order_event(payload)`, 입력 오류용 `FranchiseOrderChangeError`(`code` 속성) |
| 8.2 | `tests/test_change.py` | 요청 객체 정상 생성·입력 거부·상품 코드 앞뒤 공백 제거·값 변경 불가 검사 (DB 없음). 아직 없는 업무 판단 코드를 import하지 않음 |
| 8.3 업무 판단 | `services/franchise_order.py` | `decide_franchise_order(event, *, stock_qty, unit_price, deposit)`가 `FranchiseOrderPlan`(`franchise_id`, `prod_code`, `qty`, `total_price`, `order_status`)을 반환, 부족 시 `FranchiseOrderChangeError`, 오류 코드→HTTP 상태 표 `CHANGE_ERROR_HTTP_STATUS` |
| 8.3 | `tests/test_change.py` | 8.2 요청 검증 테스트를 보존하고 정상 판단 결과·재고 부족·예치금 부족·정확한 경계값 검사 추가 (DB 없음) |
| 8.4 저장 | `repositories/franchise_order.py` | `persist_franchise_order(plan, db)`: 한 트랜잭션으로 저장하고 주문 번호를 반환, 저장 시점 조건 불일치는 `FranchiseOrderConflict`(`code` 속성) |
| 8.4 | `tests/test_persist.py` | 인메모리 SQLite에서 정상 저장·재고 부족·예치금 부족 시 전체 취소 검사 |
| 8.5 HTTP 연결 | `routers/franchise_order.py` | 공개 `router`, `create_franchise_order(payload, db)`: 요청 해석 → 현재 값 조회 → 업무 판단 → 저장 순서로 호출하고 오류를 HTTP로 변환 |
| 8.5 | `main.py` | FastAPI `app`에 위 router 등록 |
| 8.5 마무리 | `practice_db.py` | 키트 제공 도구. `prepare`는 없는 기초 행만 추가하고 `show`는 재고·예치금·주문 건수를 출력 |

- 이름·입력·결과 형태와 위 위치를 유지하되 내부 알고리즘·SQL 매개변수 이름·테스트 보조 함수는 고정하지 않는다.
- `parse_franchise_order_event(payload)`가 받는 요청 JSON의 키는 `franchise_id`(가맹점 번호),
  `prod_code`(상품 코드), `qty`(수량)이다. 요청 객체의 같은 이름 필드에 검증한 값을 담는다.
- 8.4 저장 방식은 Chapter 12의 PostgreSQL 함수(RPC)와 같은 책임을 갖도록 다음으로 고정한다.
  - 재고와 예치금은 계산된 최종값으로 덮어쓰지 않고, SQLAlchemy `text()` SQL의 조건부 UPDATE로
    변동량만 반영한다. 재고는 `stock_qty >= 요청 수량`, 예치금은 `deposit >= 주문 금액`을 WHERE에 둔다.
  - 각 UPDATE의 영향 행 수가 1이 아니면 `FranchiseOrderConflict`를 발생시켜 저장 전체를 취소한다.
  - 주문은 `db.add()`로 추가한다. 저장 함수는 `with db.begin():` 안에서 위 작업을 모두 처리하며
    호출하기 전에 이미 시작된 트랜잭션이 없어야 한다.
  - HTTP 연결 코드는 현재 값 조회도 `with db.begin():` 블록 안에서 끝낸 뒤 저장 함수를 호출한다.
    판단에 필요한 재고·단가·예치금의 숫자 값은 조회 블록 안에서 추출한다. 블록 밖에서는 추출한 값을
    사용하며 ORM 객체의 속성을 다시 읽어 DB 조회와 트랜잭션이 시작되지 않게 한다.
  ORM 속성 대입 방식으로 바꾸려면 적용 전에 이유와 테스트 영향을 보고한다.
- 8.4 저장 테스트는 각 사례마다 새 인메모리 SQLite를 준비한다. 시작값은 상품 A001의 재고 100·단가 1000,
  가맹점 1의 예치금 50000·주문 0건이며, 데이터 준비 트랜잭션을 끝낸 뒤 저장 함수를 호출한다.
  - 정상 계획은 가맹점 1·상품 A001·수량 5·주문 금액 5000·상태 10이다. 저장 후 재고 95·예치금 45000·
    주문 1건과 반환된 주문 번호에 해당하는 기록을 확인한다.
  - 재고 부족은 정상 계획에서 수량만 101, 예치금 부족은 주문 금액만 50001로 바꾸어 저장 함수에 직접 전달한다.
    두 사례 모두 `FranchiseOrderConflict`가 발생하고 재고 100·예치금 50000·주문 0건이 유지되어야 한다.
    예치금 부족에서는 먼저 성공한 재고 차감도 취소되었는지 확인한다. 부족 사례는 업무 판단 함수를 거치지 않는다.
- HTTP 응답은 입력 오류 400, 상품·가맹점 없음 404, 재고·예치금 부족과 저장 시점 충돌 409이며
  성공은 200과 `{"status": 10}`이다. 본문이 JSON 객체가 아닌 요청의 422는 FastAPI가 처리한다.
- 기존 구현이 다른 위치·규약을 사용하면 이름을 바꾸거나 중복 생성하기 전에 충돌과 최소 변경안을 보고한다.
- `database.py`, `models.py`, `practice_db.py`, 의존성·공개 환경 예시·`_starter/`와 기존 `__init__.py`는 보존한다.
- 모든 Python·pytest 명령은 `project/`에서 실행한다. Core에서는 다음 두 테스트를 실행한다.

```powershell
python -m pytest -q tests/test_change.py
python -m pytest -q tests/test_persist.py
```

앱 등록은 `main.app`의 OpenAPI에 `POST /franchise/order`가 있는지 확인한다.
이 확인과 Mock 검증을 실제 HTTP 요청·DB 저장 검증으로 보고하지 않는다.
