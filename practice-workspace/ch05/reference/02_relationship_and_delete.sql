-- 목적: 상품 삭제 차단과 목록 제외 후 거래 연결 보존을 확인합니다.
-- 실행: 기초 실습 전용 PostgreSQL SQL Editor에서 BEGIN부터 COMMIT까지 전체 실행합니다.
-- 재실행: ch05_lab의 이 파일 전용 테이블만 삭제하고 처음부터 다시 만듭니다.
-- 보존: COMMIT 후 일반 테이블이 남아 별도 쿼리에서도 조회할 수 있습니다.
-- 범위: 다른 스키마·업무 테이블은 변경하지 않습니다. DROP 순서는 참조하는 거래가 먼저입니다.

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

-- 검사 1: 실제 DELETE를 시도한다.
-- foreign_key_violation만 예상된 차단으로 기록하고, 삭제가 성공하면 검사 실패로 처리한다.
-- 다른 오류는 잡지 않으므로 그대로 전달된다.
DO $$
BEGIN
    BEGIN
        DELETE FROM ch05_lab.lab_product WHERE code = 'A001';
        RAISE EXCEPTION '검사 실패: 거래가 참조하는 상품 A001 삭제가 성공했다';
    EXCEPTION
        WHEN foreign_key_violation THEN
            INSERT INTO ch05_lab.lab_delete_attempt (blocked, sqlstate) VALUES (true, SQLSTATE);
    END;
END $$;

-- 삭제 대신 목록 제외 표시만 바꾼다.
UPDATE ch05_lab.lab_product SET is_deleted = true WHERE code = 'A001';

-- 검사 2: 실제 조회값으로 차단 여부, 목록·전체 건수, 연결 보존을 확인한다.
-- 다르면 RAISE EXCEPTION으로 실패한다. JOIN의 상품명은 "현재" 상품명이며 당시 값 보존과는 다르다.
DO $$
DECLARE
    v_blocked  boolean;
    v_state    text;
    v_list     integer;
    v_products integer;
    v_trades   integer;
    v_trade_no text;
    v_code     text;
    v_name     text;
    v_qty      integer;
    v_deleted  boolean;
BEGIN
    SELECT blocked, sqlstate INTO v_blocked, v_state FROM ch05_lab.lab_delete_attempt;
    SELECT COUNT(*) INTO v_list     FROM ch05_lab.lab_product WHERE NOT is_deleted;
    SELECT COUNT(*) INTO v_products FROM ch05_lab.lab_product;
    SELECT COUNT(*) INTO v_trades   FROM ch05_lab.lab_trade;
    SELECT t.trade_no, p.code, p.name, t.quantity, p.is_deleted
      INTO v_trade_no, v_code, v_name, v_qty, v_deleted
      FROM ch05_lab.lab_trade t JOIN ch05_lab.lab_product p ON p.id = t.product_id;

    IF v_blocked IS DISTINCT FROM true OR v_state IS DISTINCT FROM '23503' THEN
        RAISE EXCEPTION '검사 실패: 삭제 차단 기록 기대 true/23503, 실제 %/%', v_blocked, v_state;
    END IF;
    IF v_list IS DISTINCT FROM 0 THEN
        RAISE EXCEPTION '검사 실패: 목록 건수 기대 0, 실제 %', v_list;
    END IF;
    IF v_products IS DISTINCT FROM 1 THEN
        RAISE EXCEPTION '검사 실패: 상품 건수 기대 1, 실제 %', v_products;
    END IF;
    IF v_trades IS DISTINCT FROM 1 THEN
        RAISE EXCEPTION '검사 실패: 거래 건수 기대 1, 실제 %', v_trades;
    END IF;
    IF v_trade_no IS DISTINCT FROM 'T-0001' OR v_code IS DISTINCT FROM 'A001'
       OR v_name IS DISTINCT FROM '샘플 상품' OR v_qty IS DISTINCT FROM 5
       OR v_deleted IS DISTINCT FROM true THEN
        RAISE EXCEPTION '검사 실패: 연결된 거래 값 불일치 (%, %, %, %, %)',
            v_trade_no, v_code, v_name, v_qty, v_deleted;
    END IF;
END $$;

-- 보조 결과 표: 실제 조회값을 모읍니다. COMMIT 후에도 본문의 SELECT로 다시 조회할 수 있습니다.
SELECT item, actual, expected,
       CASE WHEN actual = expected THEN 'Pass' ELSE 'Fail' END AS result
FROM (
    SELECT 1 AS ord, '삭제 차단 (blocked/SQLSTATE)' AS item,
           blocked::text || '/' || sqlstate AS actual, 'true/23503' AS expected
      FROM ch05_lab.lab_delete_attempt
    UNION ALL
    SELECT 2, '목록 건수 (제외 표시 없음)', COUNT(*)::text, '0'
      FROM ch05_lab.lab_product WHERE NOT is_deleted
    UNION ALL
    SELECT 3, '전체 상품 건수', COUNT(*)::text, '1' FROM ch05_lab.lab_product
    UNION ALL
    SELECT 4, '거래 건수', COUNT(*)::text, '1' FROM ch05_lab.lab_trade
    UNION ALL
    SELECT 5, '연결된 거래 (번호|코드|상품명|수량|제외)',
           t.trade_no || '|' || p.code || '|' || p.name || '|' || t.quantity || '|' || p.is_deleted,
           'T-0001|A001|샘플 상품|5|true'
      FROM ch05_lab.lab_trade t JOIN ch05_lab.lab_product p ON p.id = t.product_id
) AS summary
ORDER BY ord;

COMMIT;
