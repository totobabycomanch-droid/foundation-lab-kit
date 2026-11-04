# Chapter 11 연결 명세

AI가 업무 요청을 실제 DB·API·화면으로 연결할 때 읽는 고정 명세입니다.
현재 Chapter의 `AGENTS.md`와 시작 파일을 먼저 조사하고, 요청받은 단계만 구현합니다.
이 명세가 이미 생성한 코드·SQL 실행본과 다르면 덮어쓰지 말고 차이와 최소 변경안을 보고합니다.
아래 값은 실습 연결 규약이며 실제 DB 연결값은 포함하지 않습니다.

## 단계별 연결 위치

- DB 단계: 아래 테이블·함수를 만드는 SQL을 답변으로 제공합니다. AI는 DB에 접속하거나 SQL을 실행하지 않습니다.
- 독자가 성공한 생성 SQL은 `workspace/erp-project/sql/`에 번호순 실행본으로 보존합니다. AI는 API 단계에서 실행본과 적용 기록을 읽습니다.
- API 단계: `workspace/erp-project/api/main.py` 한 파일에 요청 검사·DB 호출·응답을 연결합니다. `api/__init__.py`는 시작 키트에 있습니다.
- 화면 단계: `workspace/frontend-project/src/components/ApproveOrder.vue`를 만들고 기존 `src/App.vue`에 연결합니다. 기존 개인 작업은 보존합니다.
- 기존 `requirements.txt`, `package.json`·잠금 파일과 실행 설정을 유지합니다. 새 프로젝트·별도 CSS 라이브러리는 만들지 않습니다.
- 테이블·함수 이름과 공개 입력·응답은 고정하지만 내부 함수명·화면 상태 변수명·CSS 구현은 고정하지 않습니다.

## DB 테이블

새 테이블은 참조 SQL과 같은 PostgreSQL 테이블 구조를 사용합니다. PK는 기본 키, FK는 참조 키입니다.

**stock — 현재 재고**

- `product_id`: `VARCHAR(50)`, PK.
- `quantity`: `INT NOT NULL DEFAULT 0`, `quantity >= 0` CHECK.
- `corp_id`: `VARCHAR(50) NOT NULL DEFAULT 'HQ'`.

**orders — 고정 주문**

- `order_id`: `UUID`, PK.
- `product_id`: `VARCHAR(50)`, `stock(product_id)` FK.
- `quantity`: `INT NOT NULL`, `quantity > 0` CHECK.
- `status`: `VARCHAR(20) NOT NULL DEFAULT 'CREATED'`, `'CREATED'`·`'PAID'`만 허용하는 CHECK.
- `created_at`: `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`.
- `corp_id`: `VARCHAR(50) NOT NULL DEFAULT 'HQ'`.

**stock_ledger — 재고 증감 기록**

- `ledger_id`: `BIGSERIAL`, PK.
- `product_id`: `VARCHAR(50)`, `stock(product_id)` FK.
- `qty_change`: `INT NOT NULL`. 승인 수량의 음수를 기록합니다.
- `reason`: `VARCHAR(100)`. 승인한 주문 ID를 포함한 사유를 남깁니다.
- `created_at`: `TIMESTAMP WITH TIME ZONE DEFAULT NOW()`.
- `corp_id`: `VARCHAR(50) NOT NULL DEFAULT 'HQ'`.

`corp_id`는 회사 소속 기록이며 이 장에서 회사별 접근 권한을 제한하지 않습니다.
`00_initialize_lab.sql`은 전용 DB 표식만 만들고 업무 테이블은 만들지 않습니다.
생성 SQL에 기존 객체 삭제·초기화·샘플 INSERT를 섞지 않습니다. 데이터 준비와 복원은 독자가 원고의 SQL로 수행합니다.

## 주문 승인 DB 함수

- 이름·호출 형식: `approve_order(UUID, VARCHAR, INTEGER) RETURNS VOID`.
- 매개변수: `p_order_id`, `p_product_id`, `p_qty`.
- 수량이 NULL·0 이하이면 거절합니다. 주문 없음, 저장된 주문과 상품·수량 불일치도 쓰기 전에 거절합니다.
- 검사할 주문·상품 재고 행을 `FOR UPDATE`로 잠그고, 재고가 요청 수량보다 적으면 쓰기 전에 예외로 거절합니다.
- 정상 승인에서는 재고를 요청 수량만큼 빼고 원장에 음수 증감량을 남기며 주문을 `PAID`로 바꿉니다.
- 세 쓰기는 호출한 트랜잭션에서 함께 확정·취소됩니다. 함수 내부에서 일부 쓰기만 커밋하지 않고, 예외를 성공으로 바꾸거나 삼키지 않습니다.
- 이 장에는 현재 주문 상태에 따른 재승인 거절을 추가하지 않습니다. 행 잠금·화면 잠금은 서버 재승인 방지가 아닙니다.

## 승인 API

- 실행 주소: `http://localhost:8000`, 시험 화면: `/docs`.
- 요청: `POST /orders/approve`.
- JSON 필드: `order_id`는 UUID, `product_id`는 문자열, `qty`는 1 이상 정수.
- 양수가 아닌 수량·잘못된 UUID는 요청 모델에서 DB 호출 전 `422`로 거절합니다.
- SQLAlchemy·psycopg2 동기 호출을 사용하므로 경로 함수는 일반 `def`로 작성합니다.
- DB의 `approve_order`를 매개변수 바인딩으로 호출하고, `commit()`이 끝난 뒤 HTTP `200`과 `{"status":"success"}`를 반환합니다.
- DB 호출 중 예외에서는 `rollback()`으로 트랜잭션을 정리하고 학습용 `400`의 `detail`에 원인을 전달합니다.
- 커밋 중 연결 장애는 저장 결과가 미확인일 수 있고 rollback도 실패할 수 있습니다. 모든 장애의 저장 취소나 400 응답을 보장했다고 설명하지 않습니다.
- 요청별 세션은 사용 뒤 닫습니다. 런타임 연결값은 백엔드 로컬 `.env`의 `DATABASE_URL`을 사용하되 AI는 실제 `.env`를 읽거나 API 모듈을 import하지 않습니다.
- CORS는 화면의 `http://localhost:5173`을 허용합니다. 인증·다른 업무 API는 추가하지 않습니다.

## 승인 화면

- Vue Options API와 키트의 Axios로 단일 주문 카드를 연결합니다. 앱 시작 화면에서 카드를 볼 수 있어야 합니다.
- 주문 ID·상품 ID·수량을 표시하고, 아래 고정 값으로 `order_id`·`product_id`·`qty`를 승인 API에 보냅니다.
- 요청 전 버튼 문구는 `주문 승인 API 호출`입니다. 요청 중에는 `처리 중...`과 버튼 잠금으로 추가 클릭을 막습니다.
- HTTP 200과 `status=success`를 함께 확인한 뒤 완료 메시지·`승인 완료` 버튼을 표시하고 잠금을 유지합니다.
- 오류는 완료 상태로 바꾸지 않고 `detail`을 화면 안에 표시하며 재시도할 수 있게 합니다. 다음 요청을 시작할 때 이전 오류를 지웁니다.
- 응답이 없는 오류는 `응답을 받지 못했습니다. 다시 요청하기 전에 DB에서 처리 결과를 확인하세요.`로 안내합니다.
- 응답 없는 오류와 응답의 detail을 받은 오류를 구분합니다. 실제 참조 화면의 문구·레이아웃·변수명과 완전히 같을 필요는 없습니다.
- 버튼은 키보드로 사용할 수 있어야 하고 좁은 화면에서도 주문 정보와 결과를 읽을 수 있어야 합니다.
- 프론트엔드는 포트 5173에서 실행합니다. API·DB 정의와 다른 화면은 바꾸지 않습니다.

## 고정 데이터와 직접 확인할 결과

- 주문 ID: `00000000-0000-0000-0000-000000000001`.
- 상품 ID: `PROD-100`, 저장 주문 수량·화면 요청 수량: 3.
- 기본 시작값: 주문 `CREATED`, 재고 10, 해당 상품 원장 0건.
- 정상 승인: 주문 `PAID`, 재고 7, 원장 1건·증감량 `-3`.API 성공 응답과 화면 완료를 같은 저장 결과에 대조합니다.
- 재고 부족: 주문 `CREATED`·재고 2·원장 0건에서 요청하면 `400`과 재고 부족 사유, DB 값 유지·화면 오류를 확인합니다.
- 재고 복원 뒤 같은 화면에서 한 번 재시도하는 마무리는 원고 절차를 따릅니다. 새 필수 기록이나 추가 실험을 만들지 않습니다.
- Core의 DB 중간 실패 실험은 원장에 `-3`을 막는 `tmp_block_ledger` 제약을 임시로 추가하고 함수를 직접 호출합니다. 제약 위반 뒤 `CREATED·10·0` 유지와 제약 제거를 확인하고 관찰 기록의 **DB 중간 실패** 항목에 남깁니다.
- 임시 제약은 생성 SQL에 넣지 않습니다. 독자가 본문의 고정 SQL로 추가·제거하며 API 단계 전에 제거를 확인합니다.
- 구현되어 있다는 코드 근거와 독자가 실행한 결과를 구분합니다. 중간 실패의 API·화면 처리와 추가 클릭 차단 실행은 심화 범위입니다.

## 참조와 현재 구현을 구분하기

이 명세의 구조·규약은 키트의 `chapter-reference/ch11/approve_order.sql`, `main.py`, `ApproveOrder.vue`, `App.vue`를 기준으로 확인했습니다.
독자 작업에서는 먼저 현재 열린 Chapter의 파일과 보존한 SQL 실행본을 읽습니다. 참조 코드를 통째로 복사하거나 실제 DB에 적용됐다고 추정하지 않습니다.
명세만으로 현재 구현이나 실행 결과를 확인했다고 보고하지 않습니다.
