# Chapter 8 project 규칙

<!-- common-rules-version: chapter8-v5 -->

## 작업 시작 전 (approval-required)

- `../AGENTS.md`와 `../README.md`, 이 파일을 먼저 읽는다.
- `../chapter8_order_spec.md`에서 현재 단계의 업무 조건·완료 기준과 앞 단계의 입력·반환 구조를 확인한다.
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
| 8.2 | `tests/test_change.py` | 요청 검증 테스트(DB 없음) |
| 8.3 업무 판단 | `services/franchise_order.py` | `ProductSnapshot`, `BranchOrderLinePlan`, `BranchOrderPlan`, `decide_franchise_order(event, *, products, actor_corp_id="branch01")`, `CHANGE_ERROR_HTTP_STATUS` |
| 8.3 | `tests/test_change.py` | 8.2 테스트를 보존하고 업무 판단 테스트 추가(DB 없음) |
| 8.4 저장 | `repositories/franchise_order.py` | `persist_franchise_order(plan, db)`: 마스터·상세·감사를 한 트랜잭션으로 저장하고 발주번호 반환 |
| 8.4 | `tests/test_persist.py` | 정상 저장과 실패 시 롤백 테스트(인메모리 SQLite) |
| 8.5 API 연결 | `routers/franchise_order.py` | 공개 `router`, `create_franchise_order(payload, db)`: 네 책임을 연결하고 400·409·500으로 변환 |
| 8.5 | `main.py`, `tests/test_api.py` | FastAPI 앱 등록과 API 자동 테스트 |
| 8.5 마무리 | `practice_db.py` | `prepare`는 `A001` 상품을 준비하고 `show`는 상품과 마스터·상세·감사 건수를 출력 |

이름·입력·결과 형태와 위치를 유지하되 내부 보조 함수 이름은 고정하지 않는다.

### 단계별 업무 명세

세부 조건은 [chapter8_order_spec.md](../chapter8_order_spec.md)에서 아래 항목을 읽는다.
이 파일은 공개 이름과 위치를 정하고, 업무 명세는 각 값의 의미와 동작·검증 조건을 정한다.

| 현재 단계 | 명세에서 확인할 항목 |
|---|---|
| 8.2 요청 검증 | 요청 JSON, 허용 값·기본값·오류 구분, 서버 소유 값 제외와 불변성 |
| 8.3 업무 판단 | 요청 값·상품 스냅숏·계획 구조, 서버 단가·회사 사용, VAT 계산과 오류 매핑 |
| 8.4 저장 | 실제 모델과 계획의 연결, 세션 조건, 원자적 저장과 실패·롤백 검사 |
| 8.5 API 연결 | 상품 조회와 저장 연결, 응답·오류, 자동 테스트와 실제 HTTP·DB 확인 범위 |

앞 단계의 결과는 대화 기록이 아니라 실제 구현에서 확인한다. 명세·공개 규약·구현 사이에
차이가 있으면 임의로 구조나 이름을 바꾸지 말고 충돌과 최소 변경안을 보고한다.

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
