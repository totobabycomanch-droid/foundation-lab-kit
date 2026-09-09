-- 주의: Chapter 10 전용 실습 DB에서만 실행하세요.
-- 00_initialize_lab.sql의 표식이 없으면 어떤 실습 객체도 삭제하지 않습니다.

BEGIN;

DO $$
BEGIN
    IF TO_REGCLASS('public.foundation_lab_marker') IS NULL THEN
        RAISE EXCEPTION 'Chapter 10 전용 실습 DB 표식 테이블이 없습니다. 초기화를 중단합니다.';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM public.foundation_lab_marker WHERE lab_id = 'chapter10') THEN
        RAISE EXCEPTION 'Chapter 10 전용 실습 DB 표식이 없습니다. 초기화를 중단합니다.';
    END IF;
END
$$;

DROP TABLE IF EXISTS public.order_state_history;
DROP TABLE IF EXISTS public.order_events;
DROP TABLE IF EXISTS public.stock_ledger;
DROP TABLE IF EXISTS public.order_items;
DROP TABLE IF EXISTS public.orders;
DROP TABLE IF EXISTS public.product_prices;
DROP TABLE IF EXISTS public.products;
DROP TABLE IF EXISTS public.companies;
DROP TABLE IF EXISTS public.test_orders;

COMMIT;
