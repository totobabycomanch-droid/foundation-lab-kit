# Chapter 5 작업 규칙

common-rules-version: chapter5-v5

## 진행 순서와 작업 경계

- README.md와 sql/README.md를 읽고 현재 실습을 먼저 확인한다.
- 실습 1은 웹 입력·SQLite 저장·실제 SQL 추적이다. 실습 2는 기존 Supabase SQL 세 구간이다.
- 실습 1의 생성 범위는 backend/movement_rules.py, backend/movement_write.py 두 파일뿐이다.
- 실습 2 요청 전에는 sql/02_relationship_and_delete.sql과 Supabase 데이터를 다루지 않는다.
- 실습 2의 생성 범위는 sql/02_relationship_and_delete.sql뿐이다. 실습 1의 코드와 .lab은 유지한다.
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
- 초기화는 웹 실습의 두 품목 현재고와 이력만 되돌린다. 코드와 Supabase 실습 2는 변경하지 않는다.
- UI에 현재 수량/이력을 미리 정한 값으로 채우거나 표시용 SQL을 꾸며 넣지 않는다.
- verify_observation.py와 web-baseline.json은 제공 기반 검사다. 검사 기대값이나 기준 파일을 바꾸지 않는다.
- verify_web.py는 현재 코드를 임시 사본·별도 서버·DB에서 검증한다. 시작본에는 501 미구현 응답이 있으므로 완성 기준 통과를 요구하지 않는다.
- 제공 화면은 브라우저 기본 JavaScript로 동작하며 독자가 UI 코드를 생성하는 과제는 아니다. 실제 ERP의 Vue 화면 구현은 Day에서 다룬다.

## SQL 실습 2의 실행·검사

- sql/README.md의 스키마·시작 데이터·검사·구간 주석을 따른다. 기초 실습 전용 PostgreSQL에서만 실행한다.
- 같은 파일의 세 구간을 순서대로 실행하고, 각 구간은 독립된 BEGIN·검사·COMMIT을 갖는다.
- 구간 1만 자기 테이블을 초기화한다. 구간 2·3은 직전 상태를 확인하고 앞 구간 데이터를 이어 쓴다.
- 실제 DELETE에서 foreign_key_violation(23503) 또는 restrict_violation(23001)만 처리한다. 삭제 성공과 예상 밖 오류는 실패시킨다.
- 앞 구간의 COMMIT은 뒤 구간 실패로 취소되지 않는다. 필요시 ROLLBACK하고 실패 구간 전체를 다시 실행한다.
- 완료한 구간 2·3은 반복하지 않고 처음부터 시작하려면 구간 1로 돌아간다.
- 다른 스키마·업무 테이블·함수·권한 정책과 실습 1 코드는 변경하지 않는다.
- 실습 2에서 임시 테이블·ON COMMIT DROP·DROP SCHEMA·CASCADE는 금지한다.

## 검증과 결과 설명

- 각 실습을 회의 → 조사·생성 → 직접 실행 → AI 검증 → 코드 근거 확인 → 담당자에게 결과 설명 순서로 완료한다.
- 실습 1은 화면으로 입력·현재고·이력·합계와 SQL 상세를 확인한다. 자동 수집된 실행 결과를 복사할 수 있으며 수기 기록표는 요구하지 않는다.
- SQL 상세는 SQLite 실행 콜백의 실행문·바인딩 값·확정/취소·별도 연결 재조회를 구분해 읽는다. 실행된 UPDATE도 취소되면 저장 성공이 아니다.
- 실습 1 검증 요청에서는 입고 10·출고 3, 재고 부족 거부, B001 입고 4 뒤 A001 보존을 제출된 입력·응답·재조회와 코드로 대조한다. 수량을 고정 저장하거나 이력을 빠뜨리는 코드가 없는지 확인한다.
- 실습 가상환경의 Python으로 verify_observation.py와 verify_web.py를 실행한다. 검증 요청에서는 파일을 수정하지 않고, 현재 .lab DB와 사용 중인 서버·Supabase 데이터는 변경하지 않는다. 검사는 제공된 임시 사본·별도 서버·DB를 사용한다.
- 제출 결과 검토와 직접 실행한 API·UI 검사를 나누어 보고한다. SQL을 읽은 것만으로 저장 실패·취소 시험을 통과로 판단하지 않는다. 검사를 실행하지 못했다면 Not Run과 이유를 남기고, 누락된 관찰 결과를 만들어 채우지 않는다.
- 세 업무 기준별로 확인한 결과와 아직 확인하지 못한 내용을 쉬운 말로 설명하고, 미확인 항목의 최소 보완 방법을 안내한다.
- 실습 2는 실행 상태와 조회 결과를 그대로 복사하고 구간 번호만 붙인다. 0행은 '0행'으로 남겨도 된다.
- AI는 제출 결과와 검사 코드의 적절성을 구분하고, 부족한 결과가 있으면 필요한 요청/구간만 알린다.
- 독자가 실행한 결과를 AI가 직접 실행한 것으로 보고하지 않는다. 직접 실행은 Pass·Fail·Not Run으로 구분한다.
- 브라우저를 사용하지 못했다면 UI 검사는 Not Run이다. API 검사나 코드 조사로 UI 통과를 대신하지 않는다.
- 실습 1의 업무 판단 한 곳, 실습 2의 삭제 검사 한 곳을 실제 파일 경로·함수·검색어로 안내한다.
- 선택 실패·복구 실험은 Core 필수가 아니다. SQL의 상세한 비교는 실습 2 선택 활동으로 유지한다.
- 동시성·요청 재전송 멱등성·권한 격리·사용 중지 상품 신규 거래 차단은 이번 검증 범위 밖이다.
