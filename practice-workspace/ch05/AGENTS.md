# Chapter 5 작업 규칙

common-rules-version: chapter5-v6

## 진행 순서와 작업 경계

- README.md와 sql/README.md를 읽고 현재 실습을 먼저 확인한다.
- 두 실습은 로컬 웹 입력·SQLite 저장·실제 SQL 추적이다. 실습 1과 실습 2는 별도 DB와 화면을 사용한다.
- 실습 1의 생성 범위는 backend/movement_rules.py, backend/movement_write.py 두 파일뿐이다.
- 실습 2 요청 전에는 실습 2 업무 코드를 생성하지 않는다.
- 실습 2의 생성 범위는 backend/relationship_write.py, backend/relationship_read.py뿐이다. 실습 1 업무 코드와 데이터는 유지한다.
- 회의의 합의 문장을 구현·검증·보고에서 같은 말로 사용한다. 조사 결과와 최소 변경 범위를 먼저 알린다.
- 생성 요청은 해당 범위의 구현 승인이다. 범위 밖 변경은 적용 전에 파일과 이유를 보고한다.
- reference/, _starter/와 다른 Chapter는 생성·검증의 답안으로 읽거나 복사하지 않는다.
- reference/는 막혔을 때 사용자가 명시적으로 선택하는 비교 자료다. _starter/는 복구 기준본이다.
- .env·비밀번호·API 키·JWT·운영 DB 접속 정보를 읽거나 출력하지 않는다.

## 웹 실습 1의 연결 규약

- backend/movement_rules.py의 decide_movement(direction, quantity, current_quantity)는 DB 없이 (증감 수량, 사유)를 반환한다.
- direction은 IN/OUT이다. 수량은 bool을 제외한 1~1,000,000 정수다. 입고는 양수·입고, 출고는 음수·출고 기록을 만든다.
- 남은 수량보다 많이 출고하면 contracts.MovementError(409, '남은 수량보다 많이 출고할 수 없습니다.')로 거부한다.
- backend/movement_write.py의 apply_movement(db, product_code, direction, quantity, decide_movement)는 제공된 추적 DB만 사용한다.
- db.execute(sql, parameters)는 fetchone(), fetchall(), rowcount를 지원한다. 조회 행은 컬럼명으로 읽는 dict다.
- 현재고를 읽고 decide_movement에 전달한 뒤, 해당 품목의 stock을 갱신하고 stock_history 한 행을 저장한다.
- 제품명/현재고는 products(code,name), stock(product_code,quantity), 이력은 stock_history(seq,product_code,change_qty,reason)다.
- SQL은 매개변수로 값을 전달한다. 함수 안에서 새 DB 연결·executescript·트랜잭션 확정/취소·테이블 초기화를 만들지 않는다.
- HTTP·입력 형식 검증·트랜잭션·SQLite 실행 콜백·별도 연결 재조회·화면은 제공 기능이다. 수정하지 않는다.
- 실습 1 초기화는 두 품목 현재고와 이력만 되돌린다. 코드와 실습 2의 상품·거래는 변경하지 않는다.
- UI에 현재 수량/이력을 미리 정한 값으로 채우거나 표시용 SQL을 꾸며 넣지 않는다.
- verify_observation.py와 web-baseline.json은 제공 기반 검사다. 검사 기대값이나 기준 파일을 바꾸지 않는다.
- verify_web.py는 현재 코드를 임시 사본·별도 서버·DB에서 검증한다. 시작본에는 501 미구현 응답이 있으므로 완성 기준 통과를 요구하지 않는다.
- 제공 화면은 브라우저 기본 JavaScript로 동작하며 독자가 UI 코드를 생성하는 과제는 아니다. 실제 ERP의 Vue 화면 구현은 Day에서 다룬다.

## 웹 실습 2의 연결 규약

- backend/relationship_write.py의 change_product(db, product_code, action)는 대상 상품을 조회하고 없는 상품은 MovementError(404, '상품을 찾을 수 없습니다.')로 거부한다.
- action=delete는 실제 DELETE를 실행하고 DB의 외래 키 오류를 숨기지 않는다. 거래 유무를 Python에서 확인하고 실제 DELETE 없이 차단한 것으로 보고하지 않는다.
- action=discontinue는 상품 행을 보존하고 is_deleted=1로 갱신한다. 반복해도 거래는 유지한다.
- backend/relationship_read.py의 read_relationships(db)는 {'selection': [...], 'trades': [...]}를 반환한다.
- selection은 lab_product의 is_deleted=0인 code,name을 code 순서로 읽는다. trades는 lab_trade와 lab_product를 JOIN한 trade_no,code,name,quantity,is_deleted를 trade_no 순서로 읽는다. 예전 거래를 is_deleted 조건으로 제외하지 않는다.
- DB는 lab_product(id,code,name,is_deleted), lab_trade(id,trade_no,product_id,quantity)다. lab_trade.product_id는 상품 id를 ON DELETE RESTRICT로 참조한다. 코드·이름·수량을 고정하지 않는다.
- 두 함수는 제공 db.execute(sql, parameters).fetchone()/fetchall()/rowcount를 사용한다. 연결·초기화·확정·취소·오류 변환은 제공 기반에서 담당한다.
- 입력·시작 데이터 준비·DB 제약·HTTP·화면·SQL 추적·검사는 제공 기능이다. 업무 구현 요청에서 수정하지 않는다.
- SQLite의 실제 FOREIGN KEY constraint failed만 예상한 삭제 거부다. 모든 IntegrityError를 정상 거부로 취급하지 않는다. SQLite 오류 번호와 PostgreSQL SQLSTATE를 혼용하지 않는다.
- .lab/relationships.sqlite3는 실습 2 전용이다. 준비는 기존 데이터를 덮어쓰지 않고 409로 거부한다. 실습 2 초기화는 이 DB의 거래·상품만 비우고 실습 1 DB는 유지한다.
- 관리 대상에는 취급 중단 상품도 남긴다. 새 거래용 상품 목록은 실제 조회하되 새 거래 제출 기능은 구현하지 않는다.
- reference/*.sql과 sql/README.md는 PostgreSQL 선택 참고다. 기본 웹 실습에서 SQL 파일 생성·실행이나 Supabase 연결을 요구하지 않는다.

## 검증과 결과 설명

- 각 실습을 회의 → 조사·생성 → 직접 실행 → AI 검증 → 코드 근거 확인 → 담당자에게 결과 설명 순서로 완료한다.
- 실습 1은 화면으로 입력·현재고·이력·합계와 SQL 상세를 확인한다. 자동 수집된 실행 결과를 복사할 수 있으며 수기 기록표는 요구하지 않는다.
- SQL 상세는 SQLite 실행 콜백의 실행문·바인딩 값·확정/취소·별도 연결 재조회를 구분해 읽는다. 실행된 UPDATE도 취소되면 저장 성공이 아니다.
- 실습 1 검증 요청에서는 입고 10·출고 3, 재고 부족 거부, B001 입고 4 뒤 A001 보존을 제출된 입력·응답·재조회와 코드로 대조한다. 수량을 고정 저장하거나 이력을 빠뜨리는 코드가 없는지 확인한다.
- 실습 1 검증은 가상환경의 Python으로 verify_observation.py와 verify_web.py를 실행한다. 검증 요청에서는 파일을 수정하지 않고, 현재 .lab DB와 사용 중인 서버는 변경하지 않는다. 검사는 제공된 임시 사본·별도 서버·DB를 사용한다.
- 제출 결과 검토와 직접 실행한 API·UI 검사를 나누어 보고한다. SQL을 읽은 것만으로 저장 실패·취소 시험을 통과로 판단하지 않는다. 검사를 실행하지 못했다면 Not Run과 이유를 남기고, 누락된 관찰 결과를 만들어 채우지 않는다.
- 세 업무 기준별로 확인한 결과와 아직 확인하지 못한 내용을 쉬운 말로 설명하고, 미확인 항목의 최소 보완 방법을 안내한다.
- 실습 2는 상품·거래 준비 → 실제 삭제 차단 → 취급 중단 → 선택 목록 제외·예전 거래 보존을 제출된 입력·응답·실제 SQL·재조회와 코드로 대조한다. 화면의 복사 버튼을 사용하며 수기 표는 요구하지 않는다.
- 실습 2 검증은 가상환경 Python으로 verify_observation.py와 verify_relationships.py를 실행한다. 현재 DB와 사용 중인 서버는 변경하지 않는다. 검증 중 파일은 수정하지 않는다.
- 실습 2 업무 처리·조회 코드 한 곳과 실제 삭제 차단 검사의 함수·검색어를 안내한다. 삭제 성공이나 예상 외 오류를 통과로 취급하는지 확인한다.
- AI는 제출 결과와 검사 코드의 적절성을 구분하고, 부족한 결과가 있으면 필요한 요청/구간만 알린다.
- 독자가 실행한 결과를 AI가 직접 실행한 것으로 보고하지 않는다. 직접 실행은 Pass·Fail·Not Run으로 구분한다.
- 브라우저를 사용하지 못했다면 UI 검사는 Not Run이다. API 검사나 코드 조사로 UI 통과를 대신하지 않는다.
- 실습 1의 업무 판단 한 곳, 실습 2의 삭제 검사 한 곳을 실제 파일 경로·함수·검색어로 안내한다.
- 선택 실패·복구 실험은 Core 필수가 아니다. SQL의 상세한 비교는 PostgreSQL 선택 참고로 유지한다.
- 동시성·요청 재전송 멱등성·권한 격리·사용 중지 상품 신규 거래 차단은 이번 검증 범위 밖이다.
