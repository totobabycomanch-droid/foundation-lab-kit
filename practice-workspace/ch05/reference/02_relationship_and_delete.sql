-- 기초 실습 전용 PostgreSQL SQL Editor에서 파일 전체를 실행합니다.
BEGIN;

CREATE TEMP TABLE ch05_product_example (
    product_code text PRIMARY KEY,
    product_name text NOT NULL,
    is_deleted boolean NOT NULL DEFAULT false
) ON COMMIT DROP;

CREATE TEMP TABLE ch05_trade_example (
    trade_no integer PRIMARY KEY,
    product_code text NOT NULL REFERENCES ch05_product_example(product_code),
    qty integer NOT NULL CHECK (qty > 0)
) ON COMMIT DROP;

INSERT INTO ch05_product_example VALUES ('A001', '밀가루', false);
INSERT INTO ch05_trade_example VALUES (1, 'A001', 3);

CREATE TEMP TABLE ch05_delete_check (
    delete_blocked boolean NOT NULL
) ON COMMIT DROP;

DO $$
DECLARE
    delete_blocked boolean := false;
BEGIN
    BEGIN
        DELETE FROM ch05_product_example WHERE product_code = 'A001';
    EXCEPTION WHEN foreign_key_violation THEN
        delete_blocked := true;
    END;
    IF NOT delete_blocked THEN
        RAISE EXCEPTION '거래가 참조하는 상품의 삭제가 차단되지 않았습니다.';
    END IF;
    INSERT INTO ch05_delete_check VALUES (delete_blocked);
END
$$;

UPDATE ch05_product_example SET is_deleted = true WHERE product_code = 'A001';

DO $$
BEGIN
    IF (SELECT COUNT(*) FROM ch05_product_example WHERE NOT is_deleted) <> 0
       OR (SELECT COUNT(*) FROM ch05_product_example) <> 1
       OR (SELECT COUNT(*) FROM ch05_trade_example) <> 1
       OR NOT EXISTS (
           SELECT 1 FROM ch05_trade_example t
           JOIN ch05_product_example p USING (product_code)
           WHERE t.trade_no = 1 AND t.product_code = 'A001' AND t.qty = 3
             AND p.product_name = '밀가루' AND p.is_deleted
       ) THEN
        RAISE EXCEPTION '목록 제외 후 상품·거래·참조 관계가 보존되지 않았습니다.';
    END IF;
END
$$;

-- 이름은 상품의 현재 값입니다. 당시 값 보존과 참조 관계 보존은 다른 조건입니다.
SELECT c.delete_blocked,
       (SELECT COUNT(*) FROM ch05_product_example WHERE NOT is_deleted) AS active_product_count,
       (SELECT COUNT(*) FROM ch05_product_example) AS product_count,
       (SELECT COUNT(*) FROM ch05_trade_example) AS trade_count,
       t.trade_no, p.product_code, p.product_name, t.qty, p.is_deleted
FROM ch05_delete_check c
CROSS JOIN ch05_trade_example t
JOIN ch05_product_example p USING (product_code);

COMMIT;
