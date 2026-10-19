-- 목적: 현재 수량과 입출고 이력을 비교합니다.
-- 실행: 기초 실습 전용 PostgreSQL SQL Editor에서 BEGIN부터 COMMIT까지 전체 실행합니다.
-- 재실행: ch05_lab의 이 파일 전용 테이블만 삭제하고 처음부터 다시 만듭니다.
-- 보존: COMMIT 후 일반 테이블이 남아 별도 쿼리에서도 조회할 수 있습니다.
-- 범위: 다른 스키마·업무 테이블은 변경하지 않습니다. 이 파일의 두 테이블(이력, 현재고)만 삭제합니다.

BEGIN;

CREATE SCHEMA IF NOT EXISTS ch05_lab;
DROP TABLE IF EXISTS ch05_lab.lab_stock_history;
DROP TABLE IF EXISTS ch05_lab.lab_stock;


CREATE TABLE ch05_lab.lab_stock (
    product_code text PRIMARY KEY,
    quantity     integer NOT NULL
);

CREATE TABLE ch05_lab.lab_stock_history (
    seq          integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_code text    NOT NULL,
    change_qty   integer NOT NULL,
    reason       text    NOT NULL
);

-- 현재값: 10으로 시작해 7로 갱신한다.
INSERT INTO ch05_lab.lab_stock (product_code, quantity) VALUES ('A001', 10);
UPDATE ch05_lab.lab_stock SET quantity = 7 WHERE product_code = 'A001';

-- 이력: 변경 이유를 두 행으로 남긴다.
INSERT INTO ch05_lab.lab_stock_history (product_code, change_qty, reason) VALUES
    ('A001', 10, '입고'),
    ('A001', -3, '출고');

-- 검사: 예상값이 아니라 위 테이블을 조회한 값으로 비교한다. 다르면 RAISE EXCEPTION으로 실패한다.
-- 현재값만으로는 7이 된 이유를 알 수 없고, 이력은 이유와 합계(7)를 함께 보여 준다.
DO $$
DECLARE
    v_current integer;
    v_sum     integer;
    v_rows    integer;
    v_in      integer;
    v_out     integer;
    v_in_code text;
    v_out_code text;
    v_in_reason text;
    v_out_reason text;
BEGIN
    SELECT quantity INTO v_current FROM ch05_lab.lab_stock WHERE product_code = 'A001';
    SELECT COALESCE(SUM(change_qty), 0), COUNT(*) INTO v_sum, v_rows
      FROM ch05_lab.lab_stock_history WHERE product_code = 'A001';
    -- 사유로 행을 찾지 않고 순서별로 읽어, 입고·출고가 뒤바뀐 경우도 검사한다.
    SELECT product_code, change_qty, reason INTO v_in_code, v_in, v_in_reason
      FROM ch05_lab.lab_stock_history WHERE seq = 1;
    SELECT product_code, change_qty, reason INTO v_out_code, v_out, v_out_reason
      FROM ch05_lab.lab_stock_history WHERE seq = 2;

    IF v_current IS DISTINCT FROM 7 THEN
        RAISE EXCEPTION '검사 실패: 현재 수량 기대 7, 실제 %', v_current;
    END IF;
    IF v_rows IS DISTINCT FROM 2 THEN
        RAISE EXCEPTION '검사 실패: 이력 행 수 기대 2, 실제 %', v_rows;
    END IF;
    IF v_in_code IS DISTINCT FROM 'A001' OR v_in_reason IS DISTINCT FROM '입고' THEN
        RAISE EXCEPTION '검사 실패: 이력 순서 1의 상품/사유 기대 A001/입고, 실제 %/%', v_in_code, v_in_reason;
    END IF;
    IF v_out_code IS DISTINCT FROM 'A001' OR v_out_reason IS DISTINCT FROM '출고' THEN
        RAISE EXCEPTION '검사 실패: 이력 순서 2의 상품/사유 기대 A001/출고, 실제 %/%', v_out_code, v_out_reason;
    END IF;
    IF v_in IS DISTINCT FROM 10 THEN
        RAISE EXCEPTION '검사 실패: 입고 수량 기대 10, 실제 %', v_in;
    END IF;
    IF v_out IS DISTINCT FROM -3 THEN
        RAISE EXCEPTION '검사 실패: 출고 수량 기대 -3, 실제 %', v_out;
    END IF;
    IF v_sum IS DISTINCT FROM 7 THEN
        RAISE EXCEPTION '검사 실패: 이력 합계 기대 7, 실제 %', v_sum;
    END IF;
    IF v_sum IS DISTINCT FROM v_current THEN
        RAISE EXCEPTION '검사 실패: 현재값 %와 이력 합계 %가 다름', v_current, v_sum;
    END IF;
END $$;

-- 보조 결과 표: 실제 조회값을 모읍니다. COMMIT 후에도 본문의 SELECT로 다시 조회할 수 있습니다.
SELECT item, actual, expected,
       CASE WHEN actual = expected THEN 'Pass' ELSE 'Fail' END AS result
FROM (
    SELECT 1 AS ord, '현재 수량' AS item, quantity::text AS actual, '7' AS expected
      FROM ch05_lab.lab_stock WHERE product_code = 'A001'
    UNION ALL
    SELECT 2, '이력 순서 1 (상품|수량|사유)', product_code || '|' || change_qty || '|' || reason, 'A001|10|입고'
      FROM ch05_lab.lab_stock_history WHERE seq = 1
    UNION ALL
    SELECT 3, '이력 순서 2 (상품|수량|사유)', product_code || '|' || change_qty || '|' || reason, 'A001|-3|출고'
      FROM ch05_lab.lab_stock_history WHERE seq = 2
    UNION ALL
    SELECT 4, '이력 행 수', COUNT(*)::text, '2'
      FROM ch05_lab.lab_stock_history WHERE product_code = 'A001'
    UNION ALL
    SELECT 5, '이력 합계', SUM(change_qty)::text, '7'
      FROM ch05_lab.lab_stock_history WHERE product_code = 'A001'
) AS summary
ORDER BY ord;

COMMIT;
