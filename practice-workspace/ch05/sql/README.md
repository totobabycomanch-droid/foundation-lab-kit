# Chapter 5 SQL 실행과 필수 검사

## 실행 단위와 변경 범위

기초 실습 전용 Supabase 프로젝트에서 각 파일을 BEGIN부터 COMMIT까지 전체 실행합니다.
실습 데이터는 ch05_lab 스키마의 일반 테이블에 저장합니다. COMMIT 후 다른 쿼리에서도 조회할 수 있습니다.
CREATE TEMP TABLE과 ON COMMIT DROP은 사용하지 않습니다. 업무 테이블·함수·권한 정책은 변경하지 않습니다.

각 파일은 시작할 때 CREATE SCHEMA IF NOT EXISTS ch05_lab로 전용 스키마를 준비합니다.
아래의 자기 실습 테이블만 DROP TABLE IF EXISTS로 삭제한 뒤 다시 만듭니다.
DROP SCHEMA, CASCADE, 다른 실습 테이블의 삭제는 사용하지 않습니다.

| 파일 | 초기화 대상과 삭제 순서 |
|---|---|
| 01_current_and_history.sql | ch05_lab.lab_stock_history → ch05_lab.lab_stock |
| 02_relationship_and_delete.sql | ch05_lab.lab_trade → ch05_lab.lab_delete_attempt → ch05_lab.lab_product |

두 파일은 서로 독립적입니다. 실습 2를 실행해도 실습 1의 결과가 남아 있어야 합니다.
재실행은 기존 실습 데이터를 지우고 같은 시작 데이터를 다시 만드는 것입니다.
업무 요청의 중복 처리를 방지하는 기능을 검증하는 실습은 아닙니다.
예상하지 못한 오류가 나면 원인을 확인합니다. 실패한 트랜잭션이 열려 있으면 ROLLBACK 후 전체를 다시 실행합니다.
실패하면 이전 실행 데이터가 남아 있을 수 있으므로, 남은 테이블만으로 새 실행의 성공을 판단하지 않습니다.

## 본문 SELECT와 연결할 공통 스키마

원고의 조회문이 실행되도록 아래 테이블·컬럼·데이터를 사용합니다.
검사 변수명, DO 블록 구성과 보조 결과 표의 작성 방식은 고정하지 않습니다.
추가 실습 테이블은 만들지 않습니다.

| 테이블 | 필수 컬럼과 규칙 |
|---|---|
| ch05_lab.lab_stock | product_code text 기본 키, quantity integer NOT NULL |
| ch05_lab.lab_stock_history | seq integer 기본 키, product_code text, change_qty integer, reason text; 필수 값은 NOT NULL |
| ch05_lab.lab_product | id integer 기본 키, code text UNIQUE, name text, is_deleted boolean 기본값 false; 필수 값은 NOT NULL |
| ch05_lab.lab_trade | id integer 기본 키, trade_no text UNIQUE, product_id integer 외래 키, quantity integer 양수; 필수 값은 NOT NULL |
| ch05_lab.lab_delete_attempt | blocked boolean NOT NULL, sqlstate text NOT NULL |

실습 1은 상품 A001의 현재 수량을 10에서 7로 변경합니다.
이력에는 seq 1에 입고 10, seq 2에 출고 -3을 기록합니다.
실습 2는 상품 A001·샘플 상품과 거래 T-0001·수량 5를 만듭니다.
lab_trade.product_id는 lab_product.id를 참조하며, 참조 중인 상품의 물리 삭제를 차단하도록 설정합니다.
실제 삭제 시도에서 얻은 blocked=true와 sqlstate=23503을 lab_delete_attempt에 한 행으로 남깁니다.
상품 행을 지우는 대신 is_deleted를 true로 바꾸고, 목록은 false인 상품만 조회합니다.

## 자동 검사와 독자의 직접 조회

각 파일은 실제 조회값이 잘못되면 RAISE EXCEPTION으로 실패해야 합니다.
실습 1은 현재 수량 7, 입고 10·출고 -3 두 행, 행 수 2와 이력 합계 7을 각각 검사합니다.
실습 2는 실제 DELETE를 시도합니다. foreign_key_violation만 예상 오류로 처리하고,
삭제가 성공하면 검사 실패를 발생시키며 다른 오류는 그대로 전달합니다.
목록 0건, 상품·거래 각각 1건, 기존 거래번호·상품코드·현재 상품명·수량과 제외 표시의 보존도 검사합니다.

자동 검사는 오류를 잡고, 본문의 짧은 SELECT는 독자가 업무 결과를 이해하는 데 사용합니다.
파일 끝의 실제 조회값 요약 표는 보조 근거로 유지합니다. 표를 만들기 위해 테이블을 정리하지 않습니다.
각 파일 전체를 두 번 실행하고 매번 본문의 조회를 실행해 같은 결과인지 확인합니다.
독자는 직접 조회 결과와 전체 실행·재실행 여부를 AI 검증에 전달합니다.
조회 결과만으로 앞선 검사 블록의 실행을 단정하지 않습니다.
기존 거래의 연결 조회와 실제 상품 삭제 차단 기록은 별도의 근거입니다.
상품에서 조회한 이름은 현재 이름입니다. 당시 상품명·단가를 보존하려면 거래에 별도로 남겨야 합니다.

Pass·Fail·Not Run·검사 없음으로 보고합니다. 실제 실행 근거가 없으면 DB 실행을 Pass로 보고하지 않습니다.
AI의 직접 DB 실행은 독자의 필수 완료 조건이 아닙니다.
권한 격리·동시 요청·실제 ERP의 모든 삭제 안전성은 이 실습의 검증 범위 밖입니다.

## 이전 실습 파일

.archive/와 이전 00_initialize_lab.sql·99_reset_lab.sql은 새 실습의 준비·정리에 사용하지 않습니다.
새 실습은 각 파일에 명시된 ch05_lab 테이블만 초기화합니다.
