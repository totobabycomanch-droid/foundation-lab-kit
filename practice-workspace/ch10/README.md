# Chapter 10 주문 기록 실험

이 폴더는 Chapter 10 전용 PostgreSQL 실습입니다. Chapter 9와 데이터·폴더를 이어 쓰지 않습니다.
화면과 관찰 기능은 제공하고 주문 저장 업무·업무 테스트는 AI와 완성합니다.

## 준비와 실행

1. Python 3.12를 준비합니다. erp-mini에서 `py -3.12 -m venv .venv`로 가상환경을 만들고 `.\.venv\Scripts\python.exe --version`이 Python 3.12.x인지 확인한 뒤 `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`로 설치합니다.
2. 폐기 가능한 전용 DB에서 sql/00_initialize_lab.sql, schema.sql, sql/10_seed.sql을 순서대로 실행합니다.
   schema.sql은 표식을 검사한 뒤 동명 테이블과 의존 객체를 삭제합니다. 보존할 데이터가 있는 DB에는 실행하지 않습니다.
3. .env.example을 .env로 복사하고 DATABASE_URL을 직접 설정합니다. AI에 내용을 전달하지 않습니다.
4. ch10 폴더의 PowerShell에서 `powershell -NoProfile -ExecutionPolicy Bypass -File .\start_lab.ps1`을 실행하고 http://127.0.0.1:8310을 엽니다. 실행 정책은 이 서버 프로세스에만 적용됩니다.
   또는 erp-mini에서 .venv/Scripts/python.exe -m uvicorn lab_app:app --host 127.0.0.1 --port 8310 --reload를 실행합니다.

처음에는 /orders가 501 미구현으로 안내합니다. server.py와 test_orders.py를 AI와 완성합니다.
이미 구현한 파일이 있으면 먼저 보관·비교하고 시작본으로 덮어쓰지 않습니다.

## AI가 구현할 업무와 연결 규약

- server.py의 app, OrderRequest, create_order와 POST /orders를 유지합니다.
- get_connection은 db에서 import한 공개 연결 창구입니다. 함수 안에서 재import하거나 우회 연결하지 않습니다.
- 입력은 corp_id와 items(product_id, quantity)이며 단가는 DB에서 결정합니다.
- 빈 품목·0 이하 수량은 요청 검사에서 422, 가격 없음·재고 부족은 롤백 후 400입니다.
- 성공은 200과 status=success, order_id입니다. DB 오류는 롤백 후 500이며 내부 오류를 그대로 응답하지 않습니다.
- 주문·상세·원장·이벤트·초기 CREATED 이력은 하나의 트랜잭션에서 저장합니다.
- 현재 유효한 가격을 상세의 price_snapshot에 복사합니다. 과거 주문을 현재 가격으로 갱신하지 않습니다.
- 주어진 커서의 execute(sql, parameters), fetchone/fetchall, close와 연결의 commit/rollback/close를 사용합니다.
- 관찰 커서는 한 번에 SELECT 또는 주문 관련 한 행 INSERT를 지원합니다. 대소문자·주석·줄바꿈·인용 식별자는 구문 분석으로 처리합니다.
- SQL 함수는 SUM·COUNT·NOW·gen_random_uuid와 COALESCE를 지원합니다. WITH·다중 문장·일괄 INSERT·SQL로 직접 COMMIT/ROLLBACK은 사용하지 않습니다.
- 독립 검사를 위해 테이블 이름에는 스키마를 붙이지 않습니다. 검사에서는 임시 스키마 밖 접근을 실행 전에 거절하며, 미지원 SQL은 화면의 `SQL 차단` 기록에서 확인합니다.
- test_orders.py의 미구현 테스트를 실제 업무 검사로 바꿉니다. 대역 테스트만으로 실제 PostgreSQL 롤백을 통과로 보고하지 않습니다.

제공 lab_app.py가 관찰 연결을 연결합니다. 입력·HTTP·업무 판단·SQL·확정/취소는 server.py에 함께 두고 별도 업무 계층을 추가하지 않습니다.
제공 화면·lab_store.py·lab_app.py·verify_core.py·스키마·db.py는 생성 대상이 아닙니다.
범위 밖 변경이 필요하면 적용 전에 파일과 이유를 보고합니다.

## 화면에서 확인할 순서

1. 초기 재고 100·100, 신라면 현재가 5000을 확인합니다.
2. 두 품목 정상 주문(신라면2·코카콜라1) 후 98·99, 상세 단가5000·12000과 관련 기록을 확인합니다.
3. 현재가6000 → 신라면1 새 주문 → 현재가5000 원복 후 기존/새 주문 단가5000·6000과 재고97·99를 확인합니다.
4. 신라면2·코카콜라1 입력으로 두 번째 품목 저장 실패 실험을 누릅니다.
5. 실제 SQL에서 첫 상세·원장 INSERT 뒤 SELECT 1/0의 DB 오류22012와 ROLLBACK을 확인합니다.
6. 새 연결 조회에서 주문2·상세3·원장6·이벤트2·초기 이력2와 재고97·99가 실패 전후 같은지 확인합니다.
7. 실행 결과를 복사해 AI와 검사하고, 단가 복사와 확정/취소 코드를 직접 확인한 뒤 업무 보고합니다.

실패 장치는 lab_store.ObservedCursor가 두 번째 order_items INSERT 직전에 실제 DB 오류를 내는 방식입니다.
학습자 코드의 SQL과 확정·취소 호출을 관찰하며, 제공 화면이 업무 롤백을 대신하지 않습니다.
관찰 연결의 표식 조회 취소는 업무 쓰기 시작 전의 준비이며 업무 로그에 포함하지 않습니다.
최종 값은 별도 연결의 repeatable-read 읽기입니다. 미확인 상태는 이전 표와 구분합니다.
원장은 주문 ID를 갖지 않아 상품별 전후 증감으로만 대조합니다. 다른 사용자·프로세스의 동시 쓰기가 없는 전용 DB에서 순차 실행합니다.

새로고침·서버 재시작은 DB를 초기화하지 않습니다. 탭의 복사 기록은 새로고침 전에 보관합니다.
가격 원복은 주문을 삭제하지 않습니다. 성공 주문은 클릭마다 새 주문이며 자동 재전송하지 않습니다.
인증·동시 출고·멱등성·취소·외부 이벤트 전달은 이 실습에 구현하지 않습니다.

## AI 검증과 직접 실행 대안

기본은 AI가 업무 검사와 제공 검사를 실행한 뒤 한국어로 결과를 설명하는 흐름입니다.
AI가 실행하지 못했을 때만 erp-mini의 별도 터미널에서 다음을 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_orders.py
.\.venv\Scripts\python.exe verify_core.py --allow-test-writes
```

독립 검사는 연결 대상 DB에 임의 이름의 ch10_verify_<UUID> 스키마를 만들고 검사마다 그 안의 데이터만 새로 준비합니다.
학습자의 public 주문·가격은 초기화하지 않습니다. 실행 인자는 그 임시 스키마 생성·제거만 허용합니다.
제공 관찰 연결은 SQL 구문을 분석해 다른 스키마·미지원 명령·함수를 실행 전에 차단합니다. 제공 연결 우회나 임의 Python 실행을 격리하는 보안 샌드박스는 아닙니다.
DB 접속·스키마 생성 권한이 없으면 NOT RUN, 검사 실패와 검사 준비·정리 코드의 오류는 FAIL입니다.
독립 검사는 12개이며, 주문 API 자체의 내부 오류 은닉과 화면 서버의 오류 보호를 나누어 확인합니다. 미래·종료 가격 제외와 주문별 이벤트·초기 이력의 값도 검사합니다.
강제 종료로 검사 스키마가 남았다면 정확한 이름과 대상 DB를 확인한 뒤 해당 스키마만 정리합니다.
업무 입력 사전 검사의 ‘DB 연결 없음’은 제공 관찰 조회를 제외한 주문 업무 연결을 뜻합니다.
화면에서 본 값, 실제 PostgreSQL 검사, 대역 테스트의 근거 범위를 구분해 보고합니다.

복원은 서버 종료·현재 코드 보관 후 _starter의 해당 업무 파일만 선택합니다. DB 초기화와 별도 작업입니다.
