-- 목적: 시작 상태 → 물리 삭제 차단 → 목록 제외 후 과거 거래 보존을 직접 확인합니다.
-- 실행: 아래 세 구간을 순서대로 실행합니다. 각 시작·끝 주석 사이 전체를 새 쿼리에 복사합니다.
-- 각 구간은 BEGIN부터 COMMIT까지 독립된 트랜잭션입니다. 파일 전체 실행은 학습 경로가 아닙니다.
-- 초기화: 구간 1만 실습 2의 테이블을 삭제하고 다시 만듭니다. 실습 1 테이블은 변경하지 않습니다.
-- 오류: 실패한 구간은 필요하면 ROLLBACK 후 원인 해결·해당 구간 전체 재실행합니다.
-- 이미 완료한 구간 2·3을 반복하면 사전 검사가 실패합니다. 처음부터 시작하려면 구간 1로 돌아갑니다.
-- reference 결과를 생성 SQL의 결과로 대신 보고하지 않습니다.

-- [구간 1 시작] 시작 데이터 준비
BEGIN;

CREATE SCHEMA IF NOT EXISTS ch05_lab;
DROP TABLE IF EXISTS ch05_lab.lab_trade;
DROP TABLE IF EXISTS ch05_lab.lab_delete_attempt;
DROP TABLE IF EXISTS ch05_lab.lab_product;


CREATE TABLE ch05_lab.lab_product (
    id         integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code       text    NOT NULL UNIQUE,
    name       text    NOT NULL,
    is_deleted boolean NOT NULL DEFAULT false
);

-- ON DELETE RESTRICT: 거래가 참조하는 상품의 물리 삭제를 막는다.
CREATE TABLE ch05_lab.lab_trade (
    id       integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trade_no text    NOT NULL UNIQUE,
    product_id integer NOT NULL REFERENCES ch05_lab.lab_product (id) ON DELETE RESTRICT,
    quantity integer NOT NULL CHECK (quantity > 0)
);

-- 삭제 시도의 실제 결과를 담는다. 아래 DO 블록이 시도에서 얻은 값만 기록한다.
CREATE TABLE ch05_lab.lab_delete_attempt (
    blocked   boolean NOT NULL,
    sqlstate  text    NOT NULL
);

INSERT INTO ch05_lab.lab_product (code, name) VALUES ('A001', '샘플 상품');
INSERT INTO ch05_lab.lab_trade (trade_no, product_id, quantity)
SELECT 'T-0001', id, 5 FROM ch05_lab.lab_product WHERE code = 'A001';

-- 시작 상태의 실제 데이터와 연결을 확인합니다.
DO $$
BEGIN
    IF (SELECT COUNT(*) FROM ch05_lab.lab_product) <> 1
       OR (SELECT COUNT(*) FROM ch05_lab.lab_trade) <> 1 THEN
        RAISE EXCEPTION '검사 실패: 시작 상태 상품·거래는 각각 1건이어야 합니다';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM ch05_lab.lab_trade AS t
        JOIN ch05_lab.lab_product AS p ON p.id = t.product_id
        WHERE t.trade_no = 'T-0001' AND p.code = 'A001'
          AND p.name = '샘플 상품' AND t.quantity = 5
          AND p.is_deleted = false
    ) THEN
        RAISE EXCEPTION '검사 실패: 시작 상태 거래 내용·상품 연결·목록 제외 표시가 다릅니다';
    END IF;
    IF (SELECT COUNT(*) FROM ch05_lab.lab_product WHERE is_deleted = false) <> 1 THEN
        RAISE EXCEPTION '검사 실패: 시작 상태 상품 목록 기대 1건';
    END IF;
    IF (SELECT COUNT(*) FROM ch05_lab.lab_delete_attempt) <> 0 THEN
        RAISE EXCEPTION '검사 실패: 시작 상태 삭제 시도 기록 기대 0행';
    END IF;
END $$;

-- 보조 결과는 위 검사를 대신하지 않습니다.
SELECT
    (SELECT COUNT(*) FROM ch05_lab.lab_product WHERE is_deleted = false) AS visible_products,
    (SELECT COUNT(*) FROM ch05_lab.lab_product) AS products,
    (SELECT COUNT(*) FROM ch05_lab.lab_trade) AS trades,
    (SELECT COUNT(*) FROM ch05_lab.lab_delete_attempt) AS delete_attempts;

COMMIT;
-- [구간 1 끝]

-- [구간 2 시작] 물리 삭제 시도
BEGIN;

-- 구간 1 완료 상태인지 확인합니다. 누락·반복 실행을 다음 단계로 넘기지 않습니다.
DO $$
BEGIN
    IF to_regclass('ch05_lab.lab_product') IS NULL
       OR to_regclass('ch05_lab.lab_trade') IS NULL
       OR to_regclass('ch05_lab.lab_delete_attempt') IS NULL THEN
        RAISE EXCEPTION '실행 순서 오류: 구간 1부터 실행하세요';
    END IF;
    IF (SELECT COUNT(*) FROM ch05_lab.lab_product) <> 1
       OR (SELECT COUNT(*) FROM ch05_lab.lab_trade) <> 1 THEN
        RAISE EXCEPTION '검사 실패: 구간 2 실행 전: 구간 1 완료 상태 필요, 상품·거래는 각각 1건이어야 합니다';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM ch05_lab.lab_trade AS t
        JOIN ch05_lab.lab_product AS p ON p.id = t.product_id
        WHERE t.trade_no = 'T-0001' AND p.code = 'A001'
          AND p.name = '샘플 상품' AND t.quantity = 5
          AND p.is_deleted = false
    ) THEN
        RAISE EXCEPTION '검사 실패: 구간 2 실행 전: 구간 1 완료 상태 필요, 거래 내용·상품 연결·목록 제외 표시가 다릅니다';
    END IF;
    IF (SELECT COUNT(*) FROM ch05_lab.lab_product WHERE is_deleted = false) <> 1 THEN
        RAISE EXCEPTION '검사 실패: 구간 2 실행 전: 구간 1 완료 상태 필요, 상품 목록 기대 1건';
    END IF;
    IF (SELECT COUNT(*) FROM ch05_lab.lab_delete_attempt) <> 0 THEN
        RAISE EXCEPTION '검사 실패: 구간 2 실행 전: 구간 1 완료 상태 필요, 삭제 시도 기록 기대 0행';
    END IF;
END $$;

-- 실제 삭제에서 발생한 foreign_key_violation(23503) 또는 restrict_violation(23001)만 처리합니다.
-- 내부 블록의 실패한 DELETE는 취소되지만 바깥 트랜잭션은 이어서 검사할 수 있습니다.
DO $$
BEGIN
    BEGIN
        DELETE FROM ch05_lab.lab_product WHERE code = 'A001';
        RAISE EXCEPTION '검사 실패: 거래가 참조하는 상품 A001 삭제가 성공했다';
    EXCEPTION
        WHEN foreign_key_violation OR restrict_violation THEN
            INSERT INTO ch05_lab.lab_delete_attempt (blocked, sqlstate) VALUES (true, SQLSTATE);
    END;
END $$;

-- 예상한 차단 기록과 상품·거래 보존을 실제 조회로 확인합니다.
DO $$
BEGIN
    IF (SELECT COUNT(*) FROM ch05_lab.lab_product) <> 1
       OR (SELECT COUNT(*) FROM ch05_lab.lab_trade) <> 1 THEN
        RAISE EXCEPTION '검사 실패: 삭제 차단 후 상품·거래는 각각 1건이어야 합니다';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM ch05_lab.lab_trade AS t
        JOIN ch05_lab.lab_product AS p ON p.id = t.product_id
        WHERE t.trade_no = 'T-0001' AND p.code = 'A001'
          AND p.name = '샘플 상품' AND t.quantity = 5
          AND p.is_deleted = false
    ) THEN
        RAISE EXCEPTION '검사 실패: 삭제 차단 후 거래 내용·상품 연결·목록 제외 표시가 다릅니다';
    END IF;
    IF (SELECT COUNT(*) FROM ch05_lab.lab_product WHERE is_deleted = false) <> 1 THEN
        RAISE EXCEPTION '검사 실패: 삭제 차단 후 상품 목록 기대 1건';
    END IF;
    IF (SELECT COUNT(*) FROM ch05_lab.lab_delete_attempt) <> 1 THEN
        RAISE EXCEPTION '검사 실패: 삭제 차단 후 삭제 시도 기록 기대 1행';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM ch05_lab.lab_delete_attempt
        WHERE blocked = true AND sqlstate IN ('23503', '23001')
    ) THEN
        RAISE EXCEPTION '검사 실패: 삭제 차단 기록 기대 blocked=true, SQLSTATE 23503 또는 23001';
    END IF;
END $$;

SELECT
    (SELECT COUNT(*) FROM ch05_lab.lab_product WHERE is_deleted = false) AS visible_products,
    (SELECT COUNT(*) FROM ch05_lab.lab_product) AS products,
    (SELECT COUNT(*) FROM ch05_lab.lab_trade) AS trades,
    (SELECT COUNT(*) FROM ch05_lab.lab_delete_attempt) AS delete_attempts;
SELECT blocked, sqlstate FROM ch05_lab.lab_delete_attempt;

COMMIT;
-- [구간 2 끝]

-- [구간 3 시작] 목록 제외
BEGIN;

-- 삭제 차단을 확인한 상태에서만 진행합니다. 완료한 구간 3의 반복도 실패합니다.
DO $$
BEGIN
    IF to_regclass('ch05_lab.lab_product') IS NULL
       OR to_regclass('ch05_lab.lab_trade') IS NULL
       OR to_regclass('ch05_lab.lab_delete_attempt') IS NULL THEN
        RAISE EXCEPTION '실행 순서 오류: 구간 1부터 실행하세요';
    END IF;
    IF (SELECT COUNT(*) FROM ch05_lab.lab_product) <> 1
       OR (SELECT COUNT(*) FROM ch05_lab.lab_trade) <> 1 THEN
        RAISE EXCEPTION '검사 실패: 구간 3 실행 전: 구간 2 완료 상태 필요, 상품·거래는 각각 1건이어야 합니다';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM ch05_lab.lab_trade AS t
        JOIN ch05_lab.lab_product AS p ON p.id = t.product_id
        WHERE t.trade_no = 'T-0001' AND p.code = 'A001'
          AND p.name = '샘플 상품' AND t.quantity = 5
          AND p.is_deleted = false
    ) THEN
        RAISE EXCEPTION '검사 실패: 구간 3 실행 전: 구간 2 완료 상태 필요, 거래 내용·상품 연결·목록 제외 표시가 다릅니다';
    END IF;
    IF (SELECT COUNT(*) FROM ch05_lab.lab_product WHERE is_deleted = false) <> 1 THEN
        RAISE EXCEPTION '검사 실패: 구간 3 실행 전: 구간 2 완료 상태 필요, 상품 목록 기대 1건';
    END IF;
    IF (SELECT COUNT(*) FROM ch05_lab.lab_delete_attempt) <> 1 THEN
        RAISE EXCEPTION '검사 실패: 구간 3 실행 전: 구간 2 완료 상태 필요, 삭제 시도 기록 기대 1행';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM ch05_lab.lab_delete_attempt
        WHERE blocked = true AND sqlstate IN ('23503', '23001')
    ) THEN
        RAISE EXCEPTION '검사 실패: 삭제 차단 기록 기대 blocked=true, SQLSTATE 23503 또는 23001';
    END IF;
END $$;

UPDATE ch05_lab.lab_product SET is_deleted = true WHERE code = 'A001';

-- 목록 제외 뒤에도 행과 거래 내용·연결이 남는지 확인합니다.
DO $$
BEGIN
    IF (SELECT COUNT(*) FROM ch05_lab.lab_product) <> 1
       OR (SELECT COUNT(*) FROM ch05_lab.lab_trade) <> 1 THEN
        RAISE EXCEPTION '검사 실패: 목록 제외 후 상품·거래는 각각 1건이어야 합니다';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM ch05_lab.lab_trade AS t
        JOIN ch05_lab.lab_product AS p ON p.id = t.product_id
        WHERE t.trade_no = 'T-0001' AND p.code = 'A001'
          AND p.name = '샘플 상품' AND t.quantity = 5
          AND p.is_deleted = true
    ) THEN
        RAISE EXCEPTION '검사 실패: 목록 제외 후 거래 내용·상품 연결·목록 제외 표시가 다릅니다';
    END IF;
    IF (SELECT COUNT(*) FROM ch05_lab.lab_product WHERE is_deleted = false) <> 0 THEN
        RAISE EXCEPTION '검사 실패: 목록 제외 후 상품 목록 기대 0건';
    END IF;
    IF (SELECT COUNT(*) FROM ch05_lab.lab_delete_attempt) <> 1 THEN
        RAISE EXCEPTION '검사 실패: 목록 제외 후 삭제 시도 기록 기대 1행';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM ch05_lab.lab_delete_attempt
        WHERE blocked = true AND sqlstate IN ('23503', '23001')
    ) THEN
        RAISE EXCEPTION '검사 실패: 삭제 차단 기록 기대 blocked=true, SQLSTATE 23503 또는 23001';
    END IF;
END $$;

SELECT
    (SELECT COUNT(*) FROM ch05_lab.lab_product WHERE is_deleted = false) AS visible_products,
    (SELECT COUNT(*) FROM ch05_lab.lab_product) AS products,
    (SELECT COUNT(*) FROM ch05_lab.lab_trade) AS trades,
    (SELECT COUNT(*) FROM ch05_lab.lab_delete_attempt) AS delete_attempts;
SELECT t.trade_no, p.code, p.name, t.quantity, p.is_deleted
FROM ch05_lab.lab_trade AS t
JOIN ch05_lab.lab_product AS p ON p.id = t.product_id;

COMMIT;
-- [구간 3 끝]
