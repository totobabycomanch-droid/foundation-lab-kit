# Chapter 7 웹 업무 구현과 검증 규칙

<!-- common-rules-version: chapter7-v3 -->

## 조사와 변경 범위

- README.md와 현재 파일을 조사해 해당 실습의 업무·변경 범위·검사 방법을 보고한다. 계획 요청이면 기다리고 구현 승인 후 진행한다.
- 실습 1은 transaction_example.py와 test_examples.py의 주문 검사만 완성한다. sale_example.py는 보존한다.
- 실습 2는 sale_example.py와 test_examples.py의 판매 검사를 추가한다. 주문 코드·기존 검사를 보존한다.
- reference/·_starter/를 답안으로 읽거나 복사하지 않는다. 다른 Chapter·legacy-api/·비밀 값은 읽거나 변경하지 않는다.
- Python 표준 라이브러리만 사용한다. 제공 HTTP·화면·추적·사례 준비·검사·기준 파일은 변경하지 않는다.

## 실습 1 규약

- transaction_example.py의 run_transaction(db, quantity, commit_early)를 구현한다. 이 파일의 설명과 제공 DB 규약을 따른다.
- 제공 기반은 초기 stock(prod_code,qty)의 A001과 orders(id,qty)를 준비·확정한 별도 DB를 전달한다. 입력값을 고정하지 않는다.
- 업무 코드가 BEGIN·COMMIT·ROLLBACK을 담당한다. A001 재고를 quantity만큼 줄인 뒤 commit_early=True일 때만 중간 확정한다.
- orders(qty)에 0을 INSERT해 실제 CHECK 오류를 발생시킨다. 예외를 잡아 rollback한 뒤 원래 sqlite3.IntegrityError를 다시 전달한다.
- 예외 문구나 기대 재고를 만들어 반환하지 않는다. 독립 DB의 10·수량1은 중간 확정9/함께 취소10·주문0이다. 12·수량2는 10/12다.
- test_examples.py 시작본의 미구현 실패 테스트를 실제 주문 테스트로 교체한다. 실제 오류·재고·주문·거래 종료를 단언한다. 아직 판매 구현을 요구하지 않는다.

## 실습 2 규약

- sale_example.py의 sell(db, request_key, product_code, quantity)는 판매번호 int를 반환한다. 연결·초기화는 하지 않는다.
- db.execute(sql, parameters).fetchone()/fetchall()은 dict, rowcount/lastrowid는 정수다. db.commit()/rollback()/in_transaction과 with db를 사용할 수 있다.
- stock(prod_code,qty), sales(id,request_key,prod_code,qty)를 사용한다. sales.request_key에는 DB UNIQUE 제약이 제공된다.
- 수량은 bool·문자열을 제외한 1~1,000,000의 정수만 허용하고 잘못된 입력은 LabError(422, 설명)로 거부한다.
- 같은 키·상품·수량이면 기존 번호만 반환하고 추가 차감·저장하지 않는다. 같은 키에서 상품 또는 수량만 바뀌면 LabError(409, 설명)로 거부한다.
- 새 키이면 UPDATE의 WHERE에 상품과 재고 조건을 두고 rowcount로 부족을 판단한다. 부족은 LabError(409, 설명)로 거부한다.
- 차감·판매·키 저장은 하나의 트랜잭션이다. 오류나 거부 시 이번 변경을 취소하고 원래 오류를 다시 전달한다. 업무 코드가 확정·취소한다.
- 실패 뒤 같은 DB·키로 다시 요청할 수 있어야 한다. 새 키의 같은 상품·수량은 별도 판매다. 실패 응답을 영구 보관하는 운영 정책은 이번 예제의 범위 밖이다.
- test_examples.py에 정상·동일 재시도·수량/상품 충돌·잘못된 수량·부족·정확한 소진·다른 키·실제 저장 실패 후 재요청 검사를 추가한다. 기존 주문 검사는 유지한다.
- 업무 테스트는 tempfile의 독립 DB에서 제공 lab_store.prepare·TraceDB·snapshot 또는 같은 역할의 격리된 준비·조회를 사용한다. 현재 .lab·실행 서버에 접근하지 않는다. 입력·실제 DB 조회·기대값 단언을 포함하고 연결을 정리한다.

## 제공 기능과 한계

- web_server.py가 로컬 HTTP와 화면을 연결한다. lab_store.py가 초기 준비·추적·새 연결 조회·실습 오류 장치를 제공한다.
- .lab/<세션>/에서 주문 비교는 두 독립 DB, 판매와 재시도는 같은 sale.sqlite3를 사용한다. 새로고침은 판매 DB를 초기화하지 않는다.
- 실습용 저장 오류는 제공된 SQLite 트리거로 발생시킨다. 일반적인 성공·거부 상황과 구분한다.
- 제공 서버는 열린 거래를 정리하지만 ‘미완료 거래 정리’로 표시하고 실패시킨다. 이 정리를 학습자 구현의 롤백 성공으로 보고하지 않는다.
- 같은 요청 버튼은 원래 키·입력을 전송하고 새 판매 버튼은 키만 바꾼다. 화면 표시용 HTTP request_id와 업무 request_key는 다르다.

## AI 검증과 보고

- 검증 요청에서는 파일·사용 중인 DB·서버를 수정하지 않는다. reference/는 읽지 않는다.
- 현재 실습 검증에서 verify_observation.py와 verify_web.py --exercise transaction 또는 --exercise sale을 현재 ch07/.venv의 Python으로 실행한다.
- test_examples.py의 해당 실습 검사를 실행하고 누락된 필수 조건도 조사한다. 이미 최신 실행 근거가 있다면 중복 실행은 요구하지 않는다.
- 제공 검사는 임시 사본·별도 서버·DB에서 실행한다. expectation·기준 파일을 구현 출력에 맞춰 바꾸지 않는다.
- 실제 명령·실행 결과와 제출 관찰·코드 검토를 구분한다. 업무 약속별 확인 내용·실패·미확인을 한국어로 쉽게 설명한다.
- 테스트가 없으면 ‘테스트 없음’, 미실행은 Not Run과 이유, 실제 실패는 Fail로 알린다. 시작본은 아직 완성 검사를 통과하지 않는다.
- 실제 SQL·값·commit/rollback·새 연결 DB 조회를 근거로 한다. 동시 요청·서버 강제 종료·실제 응답 유실·분산 멱등성·운영 보안을 통과로 확대하지 않는다.
- 독자가 볼 업무 코드 한 곳과 재시도 또는 롤백 테스트 한 곳을 실제 파일·함수·검색어로 안내한다. 전체 경로 표를 강요하지 않는다.
