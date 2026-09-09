-- 주의: Chapter 5 전용 실습 DB에서만 실행하세요.
-- 00_initialize_lab.sql의 표식이 없으면 어떤 실습 객체도 삭제하지 않습니다.

BEGIN;

DO $$
BEGIN
    IF TO_REGCLASS('public.foundation_lab_marker') IS NULL THEN
        RAISE EXCEPTION 'Chapter 5 전용 실습 DB 표식 테이블이 없습니다. 초기화를 중단합니다.';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM public.foundation_lab_marker WHERE lab_id = 'chapter05') THEN
        RAISE EXCEPTION 'Chapter 5 전용 실습 DB 표식이 없습니다. 초기화를 중단합니다.';
    END IF;
END
$$;

DROP FUNCTION IF EXISTS public.fn_process_order_shipment_senior(VARCHAR, BIGINT, VARCHAR);
DROP FUNCTION IF EXISTS public.process_order_approval(VARCHAR, BIGINT, VARCHAR);
DROP TABLE IF EXISTS public.loaninout20;
DROP TABLE IF EXISTS public.loanorder10;
DROP TABLE IF EXISTS public.book10;
DROP TABLE IF EXISTS public.cash_history;
DROP TABLE IF EXISTS public.stockinout20;
DROP TABLE IF EXISTS public.purchaseorder10;
DROP TABLE IF EXISTS public.product10;
DROP TABLE IF EXISTS public.stock_history;
DROP TABLE IF EXISTS public.stock_test;

COMMIT;
