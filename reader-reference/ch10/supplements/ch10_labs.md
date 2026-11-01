# Chapter 10 선택 실습

[10장 Core로 돌아가기](../README.md#return-to-book)

Core 완료 후 필요한 활동만 선택합니다. 기존 Core 기록과 선택 활동 기록을 구분하고, 실행하지 않은 항목은 Not Run으로 남깁니다.

**선택: 필수값 제약 체험과 재시작**

<a id="ch10-not-null-lab"></a>

### 작은 SQL 체험: 필수값을 빠뜨리면 어떻게 되는가?

SQL Editor나 DB 접속 도구에서 아래 SQL을 **한 단계씩 따로 실행**합니다.
3단계의 오류를 확인한 뒤에만 4단계의 정리 SQL을 실행하세요. 중간에 멈췄거나 테이블이 이미
있다는 오류가 나면 아래 [체험 중단 후 다시 시작하기](ch10_environment.md#ch10-sandbox-restart)를 따릅니다.

**1단계: 체험용 테이블 생성 (corp_id NOT NULL 규칙 강제)**
`corp_id`가 없는 행을 저장하지 못하도록 `NOT NULL`을 지정합니다.
```sql
CREATE TABLE test_orders (
    order_id INT PRIMARY KEY,
    corp_id UUID NOT NULL  -- 가맹점 식별자는 절대 비어둘 수 없음!
);
```

**2단계: 규칙에 맞는 올바른 데이터 입력 (성공)**
이 단계에서는 NULL이 아닌 UUID를 넣어 필수값 검사를 통과하는지 확인합니다.
```sql
INSERT INTO test_orders (order_id, corp_id) 
VALUES (1, '11111111-1111-1111-1111-111111111111');
-- 결과: INSERT 0 1 (성공)
```

**3단계: 필수값을 빠뜨린 데이터 입력 (NOT NULL 오류 확인)**
개발자의 실수나 코드 버그로 인해 `corp_id`가 누락된 채 주문이 생성되려 한다고 가정해 봅시다.
```sql
INSERT INTO test_orders (order_id, corp_id) 
VALUES (2, NULL);
```
다음과 비슷한 오류가 나며 행이 저장되지 않아야 합니다. PostgreSQL 버전에 따라 `of relation "test_orders"`
같은 표현과 `DETAIL` 줄이 더 붙을 수 있으며, `NOT NULL` 제약 위반이라는 내용이 같으면 정상입니다.
```text
ERROR: null value in column "corp_id" violates not-null constraint
(에러: "corp_id" 컬럼의 NULL 값이 NOT-NULL 제약 조건을 위반했습니다.)
```

**4단계: 체험 완료 후 깔끔하게 정리하기**
체험이 끝나면 다음 쿼리로 임시 테이블을 정리합니다.
```sql
DROP TABLE test_orders;
```

> **[결과 해석]**
> 이 체험은 `corp_id`의 NULL 저장을 DB가 거절한다는 점을 보여줍니다. 다른 회사 ID를 넣는 요청이나 권한 없는 조회에는 별도의 접근 검사가 필요합니다.

---

<a id="ch10-snapshot-lab"></a>

**선택 체험: 10.4.2 원칙 관찰**

> [!TIP]
> **[DDL 샌드박스: 가격 변동 시 단가 보존 검증]**
>
> **1. 준비·실행**
>
> SQL Editor나 PostgreSQL 접속 도구에서 이 블록만 먼저 실행합니다. 테이블과 데이터를 만들고 상품 가격을 바꿉니다.
>
> ```sql
> -- 1단계: 임시 상품 및 주문상세 테이블 생성
> CREATE TABLE temp_sandbox_products (product_id INT PRIMARY KEY, price INT);
> CREATE TABLE temp_sandbox_order_items (item_id INT PRIMARY KEY, product_id INT, price_snapshot INT);
> 
> -- 2단계: 상품 정보 등록 및 주문 당시 단가 저장
> INSERT INTO temp_sandbox_products VALUES (101, 1000);
> INSERT INTO temp_sandbox_order_items VALUES (1, 101, 1000); -- 주문 당시 단가 1000원 저장
> 
> -- 3단계: 오늘 신라면 단가 인상 (1000원 -> 1200원)
> UPDATE temp_sandbox_products SET price = 1200 WHERE product_id = 101;
>
> ```
>
> **2. 결과 관찰**
>
> 아래 SELECT만 실행합니다. `order_price = 1000`, `current_price = 1200`인 결과를 확인하고 기록하세요.
>
> ```sql
> -- 4단계: 어제 주문의 단가와 오늘의 상품 가격을 나란히 조회
> SELECT i.price_snapshot AS order_price, p.price AS current_price
> FROM temp_sandbox_order_items i
> JOIN temp_sandbox_products p ON p.product_id = i.product_id
> WHERE i.product_id = 101;
> -- 결과: order_price = 1000, current_price = 1200
> -- 상품 가격은 바뀌었지만 기존 주문 단가는 그대로 유지됩니다.
> -- 같은 JOIN에서 p.price로 금액을 계산하면 어제 주문이 1200원으로 계산됩니다.
>
> ```
>
> **3. 정리**
>
> 결과를 기록했다면 아래 SQL로 이번 체험의 두 테이블을 정리합니다.
>
> ```sql
> -- 5단계: 임시 테이블 정리
> DROP TABLE temp_sandbox_order_items;
> DROP TABLE temp_sandbox_products;
> ```
>
> 중간에 멈췄다면 [체험 중단 후 다시 시작하기](ch10_environment.md#ch10-sandbox-restart)를 따릅니다.

---

<a id="ch10-ledger-lab"></a>

**선택 체험: 10.4.3 원칙 관찰**

> [!TIP]
> **[DDL 샌드박스: 원장 추가 기록과 합계 확인]**
>
> **1. 준비·실행**
>
> SQL Editor나 PostgreSQL 접속 도구에서 이 블록만 먼저 실행합니다. 원장에 입고와 출고를 차례로 기록합니다.
>
> ```sql
> -- 1단계: 임시 재고 수불부 원장 테이블 생성 (일련번호 자동 증가)
> CREATE TABLE temp_sandbox_ledger (
>     ledger_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
>     product_id INT,
>     quantity_change INT -- 입고(+), 출고(-)
> );
> 
> -- 2단계: 재고 덮어쓰기(UPDATE) 없이 계속해서 이력만 추가(INSERT)
> INSERT INTO temp_sandbox_ledger (product_id, quantity_change) VALUES (201, 100); -- 신라면 100개 입고
> INSERT INTO temp_sandbox_ledger (product_id, quantity_change) VALUES (201, -2);   -- 신라면 2개 출고
> INSERT INTO temp_sandbox_ledger (product_id, quantity_change) VALUES (201, -5);   -- 신라면 5개 출고
>
> ```
>
> **2. 결과 관찰**
>
> 아래 SELECT만 실행해 `current_stock = 93`인지 확인하고 기록합니다. 순서대로 넣은 세 기록의 합계이며, 동시성 테스트는 아닙니다.
>
> ```sql
> -- 3단계: 현재 실시간 최종 재고량 합산(SUM) 계산
> SELECT SUM(quantity_change) AS current_stock FROM temp_sandbox_ledger WHERE product_id = 201;
> -- 결과: 93 (순서대로 기록한 세 건의 합계. 동시성 안전성 검증은 아님)
>
> ```
>
> **3. 정리**
>
> 합계를 기록했다면 아래 SQL로 이번 체험의 테이블을 정리합니다.
>
> ```sql
> -- 4단계: 임시 테이블 정리
> DROP TABLE temp_sandbox_ledger;
> ```
>
> 중간에 멈췄다면 [체험 중단 후 다시 시작하기](ch10_environment.md#ch10-sandbox-restart)를 따릅니다.

---

<a id="ch10-delete-lab"></a>

**선택 체험: 10.4.4 원칙 관찰**

> [!TIP]
> **[DDL 샌드박스: 취소 상태와 논리 삭제 표시 체험]**
>
> **1. 준비·실행**
>
> SQL Editor나 PostgreSQL 접속 도구에서 이 블록만 먼저 실행합니다. 주문을 만든 뒤 취소 상태로 바꿉니다.
>
> ```sql
> -- 1단계: 임시 주문 테이블 생성 및 상태 제약
> CREATE TABLE temp_sandbox_orders (
>     order_id INT PRIMARY KEY,
>     order_status TEXT CHECK (order_status IN ('CREATED', 'PAID', 'CANCELLED')),
>     deleted_at TIMESTAMP
> );
> 
> -- 2단계: 테스트 주문 생성
> INSERT INTO temp_sandbox_orders VALUES (1, 'CREATED', NULL);
> 
> -- 3단계: 주문 취소 상태만 기록
> UPDATE temp_sandbox_orders 
> SET order_status = 'CANCELLED'
> WHERE order_id = 1;
>
> ```
>
> **2. 취소 결과 관찰**
>
> 아래 SELECT만 실행합니다. 행은 1개이고 `order_status = CANCELLED`, `deleted_at = NULL`인지 확인합니다.
>
> ```sql
> -- 4단계: 취소 후에도 행이 남고, 논리 삭제 표시는 비어 있는지 확인
> SELECT * FROM temp_sandbox_orders;
> -- 결과: 1행, order_status는 CANCELLED, deleted_at은 NULL
>
> ```
>
> **3. 논리 삭제 표시**
>
> 취소 후에도 행이 남은 것을 확인했다면, 이번에는 일반 목록에서 제외할 표시를 넣습니다.
>
> ```sql
> -- 5단계: 취소와 별개로, 일반 목록에서 제외할 논리 삭제 표시
> UPDATE temp_sandbox_orders SET deleted_at = CURRENT_TIMESTAMP WHERE order_id = 1;
>
> ```
>
> **4. 목록 제외 결과 관찰**
>
> 아래 SELECT만 실행해 0행인지 확인합니다. 아직 정리 SQL은 실행하지 않습니다.
>
> ```sql
> -- 6단계: 목록 제외와 원본 보존을 각각 확인
> SELECT * FROM temp_sandbox_orders WHERE deleted_at IS NULL;
> -- 결과: 0행. 위 조회 조건이 논리 삭제 표시가 있는 행을 제외함
> ```
>
> **5. 원본 보존 결과 관찰**
>
> 아래 SELECT를 따로 실행합니다. 원본 1행과 `CANCELLED` 상태·논리 삭제 시각을 확인하고, 앞의 0행 결과와 함께 기록합니다.
>
> ```sql
> SELECT * FROM temp_sandbox_orders;
> -- 결과: 1행. CANCELLED 상태와 deleted_at 시각을 가진 원본이 남음
>
> ```
>
> **6. 정리**
>
> 두 조회 결과를 기록했다면 아래 SQL로 이번 체험의 테이블을 정리합니다.
>
> ```sql
> -- 7단계: 임시 테이블 정리
> DROP TABLE temp_sandbox_orders;
> ```
>
> 중간에 멈췄다면 [체험 중단 후 다시 시작하기](ch10_environment.md#ch10-sandbox-restart)를 따릅니다.

---

<a id="ch10-optional-errors"></a>
<a id="ch10-extra-records"></a>
<a id="ch10-empty-items-lab"></a>

## 입력 거절과 중간 저장 실패를 구분하기

Core의 양수 입력·두 번째 저장 실패는 DB에 일부 쓰기가 진행된 뒤의 전체 취소 실험입니다.
품목 없음과 수량0은 422로 먼저 거절되므로 DB CHECK와 중간 롤백의 증거가 아닙니다.
Swagger를 사용할 때는 http://127.0.0.1:8310/docs의 POST /orders에서 items=[] 또는 수량0을 요청하고 구분해 보세요.
존재하지 않는 회사 ID는 DB FK 오류, 가격 없는 상품과 재고 부족은 업무 오류입니다.
한 사례씩 실제 응답·관찰 SQL·전후값을 비교하고 예상 밖의 결과면 다음 요청을 멈춥니다.

DB CHECK 자체를 보고 싶다면 별도 SQL 체험용 테이블에 CHECK(quantity > 0)를 만들고 0을 저장해 비교하세요.
기존 입력 검사를 제거하거나 Core 테이블의 제약을 바꾸지 않습니다.

<a id="ch10-independent-checks"></a>

## 독립 검사 직접 실행

AI가 이미 실행했다면 반복하지 않습니다. 직접 실행할 때는 `erp-mini` 폴더의 별도 PowerShell 터미널에서 다음 명령을 사용합니다. 실행 중인 서버 터미널에는 입력하지 않습니다.
새 터미널의 위치가 `ch10`이라면 먼저 `cd .\erp-mini`로 이동합니다. 가상환경 활성화 스크립트는 실행하지 않습니다.

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_orders.py
.\.venv\Scripts\python.exe verify_core.py --allow-test-writes
```

한 줄씩 실행합니다. 첫 명령의 업무 테스트가 `OK`인지 확인한 뒤 두 번째 명령을 실행합니다. 실패하면 AI와 원인을 해결한 뒤 다시 확인합니다.

독립 검사는 별도 임시 스키마의 실제 PostgreSQL을 사용합니다. 원래 실습 주문과 가격을 지우지 않습니다.
검사 스키마를 만들 권한이 없거나 DB에 연결하지 못하면 NOT RUN이며, 실행된 검사의 실패는 FAIL입니다.
시작본의 501과 미구현 업무 테스트는 정상 구현을 완료했다는 뜻이 아닙니다.

<a id="ch10-commit-boundary-lab"></a>

## 첫 품목을 먼저 커밋하면 무엇이 남을까?

이 대조 실험은 Core와 분리한 새 작업 폴더와 새 전용 DB에서만 진행합니다.
현재 실습 코드·관찰 기록을 보관하고 새 폴더에서 동일 규칙의 주문 구현과 화면을 준비합니다.
정상 주문은 보내지 않고 재고100·100, 건수0·0·3·0·0을 확인합니다.

1. 두 번째 품목 저장 실패 실험을 실행합니다. 첫 품목 쓰기 뒤 오류22012이며 전후값이 같은지 확인합니다.
2. AI에게 이 복사본의 주문 업무에서 첫 품목 상세·원장 쓰기가 끝난 뒤 커밋하는 최소 변경을 요청합니다.
3. 다른 입력·실패 장치·예외 처리를 유지하고 같은 실패 실험을 다시 실행합니다.
4. 주문1·상세1·원장4·이벤트0·이력0, 재고98·100이 남는지 실제 조회로 확인합니다. 기본 입력 신라면2·코카콜라1 기준입니다.

중간 확정한 기록은 뒤의 롤백으로 취소할 수 없습니다. 이 결과는 의도적으로 잘못된 코드의 동작을 비교한 것입니다.
Core의 생성물을 이 코드로 덮어쓰지 않습니다. 새 DB의 실험 데이터만 남기고 서버를 종료합니다.

<a id="ch10-ai-build-lab"></a>

## AI 생성 결과가 예상과 다를 때

AI 생성은 이제 Core에서 수행합니다. 제공 서버로 교체해 결과를 맞추기보다 실제 실패 행을 전달해 원인을 조사합니다.

```text
AGENTS.md와 주문 코드·테스트를 조사하고 아래 관찰값이 업무 규칙과 다른 이유를 설명하세요.
첫 DB 쓰기, 오류 위치, 커밋·롤백 경계와 저장 후 새 연결 조회를 구분하세요.
관찰한 사실과 추정을 나누고 최소 수정 범위와 재검증 방법을 보고하세요.
아직 파일은 수정하지 말고 .env·연결 문자열·비밀번호를 읽거나 출력하지 마세요.

[실제 실패 행과 관찰값]
여기에 필요한 실제 결과만 붙입니다.
```

조사 근거를 확인한 뒤 최소 수정과 해당 사례의 재검증을 요청합니다. 이미 통과한 검사를 이유 없이 반복하지 않습니다.
