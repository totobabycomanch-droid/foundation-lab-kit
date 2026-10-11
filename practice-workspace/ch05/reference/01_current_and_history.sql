-- 기초 실습 전용 PostgreSQL SQL Editor에서 파일 전체를 실행합니다.
BEGIN;

CREATE TEMP TABLE ch05_current_example (
    product_code text PRIMARY KEY,
    qty integer NOT NULL
) ON COMMIT DROP;

CREATE TEMP TABLE ch05_history_example (
    sequence_no integer PRIMARY KEY,
    product_code text NOT NULL,
    qty integer NOT NULL CHECK (qty <> 0),
    reason text NOT NULL
) ON COMMIT DROP;

INSERT INTO ch05_current_example VALUES ('A001', 10);
UPDATE ch05_current_example SET qty = 7 WHERE product_code = 'A001';
INSERT INTO ch05_history_example VALUES
    (1, 'A001', 10, '입고'),
    (2, 'A001', -3, '출고');

DO $$
BEGIN
    IF (SELECT qty FROM ch05_current_example WHERE product_code = 'A001')
       IS DISTINCT FROM 7 THEN
        RAISE EXCEPTION '현재값은 7이어야 합니다.';
    END IF;
    IF (SELECT SUM(qty) FROM ch05_history_example) IS DISTINCT FROM 7
       OR (SELECT COUNT(*) FROM ch05_history_example) <> 2
       OR NOT EXISTS (SELECT 1 FROM ch05_history_example WHERE sequence_no = 1 AND qty = 10)
       OR NOT EXISTS (SELECT 1 FROM ch05_history_example WHERE sequence_no = 2 AND qty = -3) THEN
        RAISE EXCEPTION '입고 10·출고 -3과 합계 7을 확인하지 못했습니다.';
    END IF;
END
$$;

-- 실제 이력의 내용과 집계값을 한 표로 모아 검토할 결과를 보여 줍니다.
SELECT c.product_code, c.qty AS current_qty,
       h.history_count, h.history_entries, h.history_total
FROM ch05_current_example c
JOIN (
    SELECT product_code, COUNT(*) AS history_count,
           STRING_AGG(reason || ' ' || qty::text, ' / ' ORDER BY sequence_no) AS history_entries,
           SUM(qty) AS history_total
    FROM ch05_history_example
    GROUP BY product_code
) h USING (product_code);

COMMIT;
