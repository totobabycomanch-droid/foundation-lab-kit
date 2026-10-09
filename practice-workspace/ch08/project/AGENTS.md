# Chapter 8 project 규칙

<!-- common-rules-version: chapter8-v4 -->

## 작업 시작 전 (approval-required)

- `../AGENTS.md`와 `../README.md`, 이 파일을 먼저 읽는다.
- 요구사항, 기존 파일, 변경 범위와 검증 방법을 먼저 보고하고 독자의 승인 뒤에만 변경한다.
- 승인된 현재 단계의 파일만 최소 변경하고 이전 단계 결과와 시작 파일을 보존한다.

## 보안과 검증 근거 (secrets-protected, evidence-scoped)

- `.env`, 비밀번호, API key, JWT와 실제 DB URL을 읽거나 출력하지 않는다.
- 결과는 `Pass`, `Fail`, `Not Run`, `테스트 없음`으로 구분하고 코드 검토인지 명령 실행인지 밝힌다.
- 실행하지 않은 테스트를 통과로 추정하지 않는다.
- 검증 보고는 확인할 질문·판정·근거의 표로 작성한다. 근거는 `AI 실행:`, `독자 제공 실행 결과:`,
  `코드 검토:` 중 하나로 시작한다. 독자 제공 결과를 AI가 직접 실행한 결과로 표시하지 않는다.
- `Fail`·`Not Run`·`테스트 없음`은 원인, 다음 확인 방법과 독자가 직접 볼 최소 코드 한 곳을 덧붙인다.
- Mock은 전달값·호출·오류 전파의 근거이며 실제 DB 저장·롤백·HTTP 성공의 근거가 아니다.

## 구현 책임

- 요청 검증과 업무 판단은 `services/`에 두고 DB에 접근하지 않는다.
- API 연결은 `routers/`에서 요청 검증 → 상품 조회 → 업무 판단 → 저장 순서로 조립한다.
- 저장은 `repositories/`에 두고 발주 마스터·상세·감사를 한 트랜잭션으로 처리한다.
- 발주 마스터·상세·감사만 저장하고 상품 단가·활성 상태는 변경하지 않는다.
- 이번 실습에 없는 모델·업무 규칙을 추가하지 않는다.
- 회사·거래처·상태·단가·금액은 서버 소유 값이다. 클라이언트가 같은 이름의 값을 보내도 신뢰하지 않는다.
- `.env.example`의 변수 이름만 참고하며 Core에서는 로컬 SQLite만 사용한다.
- 변경 뒤 현재 단계의 확인 명령을 실행한다.

## 교육용 파일 위치와 공개 연결 규약

경로는 `project/` 기준이다. 먼저 기존 파일을 조사하고 현재 단계의 파일만 생성·수정한다.
아직 없는 후속 단계 파일은 시작 키트의 결함이 아니다.

| 단계 | 파일 | 공개 규약과 역할 |
|---|---|---|
| 8.2 요청 검증 | `services/franchise_order.py` | `BranchOrderItemEvent`, `BranchOrderEvent`, `parse_franchise_order_event(payload)`, `FranchiseOrderChangeError(code, message)` |
| 8.2 | `tests/test_change.py` | 최소 마스터·상세 정상화, 서버 소유 값 폐기, 잘못된 입력·중복 품목·불변 객체 검사(DB 없음) |
| 8.3 업무 판단 | `services/franchise_order.py` | `ProductSnapshot`, `BranchOrderLinePlan`, `BranchOrderPlan`, `decide_franchise_order(event, *, products, actor_corp_id="branch01")`, `CHANGE_ERROR_HTTP_STATUS` |
| 8.3 | `tests/test_change.py` | 8.2 테스트를 보존하고 서버 단가·공급가액·VAT·합계, 상품 없음·비활성·잘못된 단가 검사(DB 없음) |
| 8.4 저장 | `repositories/franchise_order.py` | `persist_franchise_order(plan, db)`: 마스터·상세·감사를 한 트랜잭션으로 저장하고 발주번호 반환 |
| 8.4 | `tests/test_persist.py` | 정상 1·1·1 저장과 상세·감사 INSERT 실패의 0·0·0 롤백 검사(인메모리 SQLite) |
| 8.5 API 연결 | `routers/franchise_order.py` | 공개 `router`, `create_franchise_order(payload, db)`: 네 책임을 연결하고 400·409·500으로 변환 |
| 8.5 | `main.py`, `tests/test_api.py` | FastAPI 앱 등록, 고정 성공 응답, 오류 상태와 안전한 메시지 검사 |
| 8.5 마무리 | `practice_db.py` | `prepare`는 `A001` 상품을 준비하고 `show`는 상품과 마스터·상세·감사 건수를 출력 |

이름·입력·결과 형태와 위치를 유지하되 내부 보조 함수 이름은 고정하지 않는다.

### 요청과 계산 규약

- 요청은 `master` 객체와 비어 있지 않은 `details` 배열로 구성한다.
- `master`의 Core 필드는 `dept_code`, `emp_code`, 양의 정수 `delivery_code`, `1|2`인 `is_vat`이다.
- 각 상세는 1~50자의 `prod_code`와 양의 정수 `qty`만 사용하며 같은 상품을 중복할 수 없다.
- `corp_id`, `partner_id`, `order_status`, `unit_price`, `total_amount` 등 서버 소유 입력은 버린다.
- 상품 없음·비활성은 `product_not_found` 400, 0 이하 서버 단가는 `invalid_unit_price` 409로 변환한다.
- 단가 1,000원·수량 5·`is_vat="2"`의 공급가액은 5,000원, VAT는 500원, 합계는 5,500원이다.
- VAT는 공급가액의 10%를 1원 단위로 반올림하며 0.5원은 올린다. 공급가액 1,005원이면 VAT는 101원이다.
- 계획의 회사·거래처·상태는 `branch01`, `admin`, `"10"`이다. 발주번호는 저장 시 DB가 만든다.

### 8.4 저장과 테스트 규약

- 모델은 `Product`, `PurchaseOrder`, `PurchaseOrderDetail`, `AuditLog`를 사용한다.
- 저장 함수는 `with db.begin():`에서 마스터 flush → 상세 전체 flush → 감사 flush 순서로 처리한다.
- 상세와 감사 실패는 SQLAlchemy 테스트 이벤트로 각 INSERT 시점에 유도한다. 제품 코드에 실패 스위치를 넣지 않는다.
- 정상 시작값은 상품 `A001`, 단가 1,000원, 활성 상태와 세 저장 테이블 0·0·0건이다.
- 정상 저장은 마스터·상세·감사 1·1·1건과 합계 5,500원, 상품 단가·활성 상태 불변을 확인한다.
- 여러 상세의 정상 저장에서 모든 상세 값·번호 연결과 감사 건수·총액이 계획과 일치해야 한다.
- 상세 또는 감사 실패 뒤 새 세션으로 세 저장 테이블이 모두 0·0·0건인지 확인한다.
- 뒤쪽 상세 실패 전에 앞선 INSERT의 실제 실행 완료 근거를 확인하고, 확인되지 않으면 보장 범위를 제한해 보고한다.
- 테스트 이벤트는 실패해도 제거한다. 이벤트 구현 분석은 독자의 필수 완료 조건이 아니다.

### 8.5 API 연결 규약

- 상품 조회를 `with db.begin():` 안에서 끝내고 필요한 값을 `ProductSnapshot`으로 추출한 뒤 판단한다.
- 저장은 `persist_franchise_order(plan, db)` 한 번으로 수행한다. 마스터·상세·감사를 여러 HTTP 요청으로 나누지 않는다.
- 성공은 HTTP 200과 `status`, `purchase_order_no`, `order_status`, `detail_count`, `total_amount`를 반환한다.
- 입력·중복·상품 없음은 400, 잘못된 서버 단가와 무결성 충돌은 409, 예상하지 못한 저장 오류는 500이다.
- 500 응답에 SQL과 내부 예외 문자열을 노출하지 않는다.
- 교육용 경로는 `POST /franchise/order`다. 실제 제품 경로, JWT, `Idempotency-Key`, 마감과 동시성 제어를
  구현했거나 검증했다고 주장하지 않는다. 기존 발주 없음 404는 신규 등록 Core 범위가 아니다.

## 공통 보존과 실행

- 기존 구현이 다른 위치·규약을 사용하면 중복 생성 전에 충돌과 최소 변경안을 보고한다.
- `database.py`, `models.py`, `practice_db.py`, 의존성·공개 환경 예시·`_starter/`와 기존 `__init__.py`는 보존한다.
- Python·pytest 명령은 `project/`에서 실행한다. Core에서는 단계에 따라 다음 파일을 실행한다.

```powershell
python -m pytest -q tests/test_change.py
python -m pytest -v tests/test_persist.py
python -m pytest -q tests/test_api.py
```

앱 등록은 `main.app`의 OpenAPI에서 `POST /franchise/order`를 확인한다. 앱 등록과 Mock만으로 실제 HTTP
요청 또는 파일 DB 저장이 성공했다고 판정하지 않는다.
