-- Chapter 11 전용 DB의 실습 객체를 모두 지웁니다. A·B 재준비용이 아닙니다.
-- 서버를 멈추고 프로젝트를 확인한 뒤 실행합니다. DO 전체가 성공하거나 함께 취소됩니다.
-- Supabase 관리 스키마·확장 객체는 삭제하지 않습니다. CASCADE는 사용하지 않습니다.
DO $clear_ch11$
BEGIN
    IF to_regclass('public.foundation_lab_marker') IS NULL THEN
        RAISE EXCEPTION USING ERRCODE = 'P1120', MESSAGE = 'chapter11_marker_required';
    END IF;
    IF (SELECT count(*) FROM public.foundation_lab_marker) <> 1
       OR NOT EXISTS (SELECT 1 FROM public.foundation_lab_marker WHERE lab_id = 'chapter11') THEN
        RAISE EXCEPTION USING ERRCODE = 'P1121', MESSAGE = 'chapter11_marker_mismatch';
    END IF;

    -- 지정 테이블과 그 테이블에 소유된 시퀀스 외의 객체가 있으면 보존하고 중단합니다.
    IF EXISTS (
        SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p', 'v', 'm', 'f', 'S')
          AND c.relname NOT IN ('stock', 'orders', 'stock_ledger', 'foundation_lab_marker', 'ch11_sql_history')
          AND NOT (c.relkind = 'S' AND EXISTS (
              SELECT 1 FROM pg_depend d
              JOIN pg_class owner_table ON owner_table.oid = d.refobjid
              JOIN pg_namespace owner_ns ON owner_ns.oid = owner_table.relnamespace
              WHERE d.classid = 'pg_class'::regclass AND d.objid = c.oid
                AND d.refclassid = 'pg_class'::regclass AND d.deptype IN ('a', 'i')
                AND owner_ns.nspname = 'public'
                AND owner_table.relname IN ('stock', 'orders', 'stock_ledger', 'foundation_lab_marker', 'ch11_sql_history')
          ))
    ) THEN
        RAISE EXCEPTION USING ERRCODE = 'P1122', MESSAGE = 'unexpected_objects_preserved';
    END IF;

    -- 다른 함수나 다른 매개변수 형식의 함수를 이름만 보고 삭제하지 않습니다.
    IF EXISTS (
        SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public'
          AND NOT EXISTS (
              SELECT 1 FROM pg_depend d WHERE d.classid = 'pg_proc'::regclass
                AND d.objid = p.oid AND d.deptype = 'e'
          )
          AND NOT (p.prokind = 'f' AND p.prorettype = 'void'::regtype AND (
              (p.proname = 'approve_order' AND oidvectortypes(p.proargtypes) = 'uuid, character varying, integer')
              OR (p.proname = 'change_order_quantity' AND oidvectortypes(p.proargtypes) = 'uuid, integer')
          ))
    ) THEN
        RAISE EXCEPTION USING ERRCODE = 'P1123', MESSAGE = 'unexpected_functions_preserved';
    END IF;

    DROP FUNCTION IF EXISTS public.change_order_quantity(UUID, INTEGER);
    DROP FUNCTION IF EXISTS public.approve_order(UUID, VARCHAR, INTEGER);
    DROP TABLE IF EXISTS public.stock_ledger;
    DROP TABLE IF EXISTS public.orders;
    DROP TABLE IF EXISTS public.stock;
    DROP TABLE IF EXISTS public.ch11_sql_history;
    DROP TABLE IF EXISTS public.foundation_lab_marker;
END;
$clear_ch11$;
