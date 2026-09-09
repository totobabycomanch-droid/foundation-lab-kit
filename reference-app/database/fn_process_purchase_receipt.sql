-- Day 17/18: 가맹점 입고 확정(40 -> 60) 원자 저장 RPC
-- 실행 대상: 로컬 또는 개발용 Supabase SQL Editor
-- 실행 금지: 운영 DB
-- 사전 설치: fn_update_stock_atomic.sql

BEGIN;

-- Day 24 F120이 조회할 본사 매출채권 원장. Day 18 입고확정이 채권의 발생 사건이다.
CREATE TABLE IF NOT EXISTS public.franchise_receivable10 (
    id UUID PRIMARY KEY DEFAULT pg_catalog.gen_random_uuid(),
    stock_inbound_no BIGINT NOT NULL UNIQUE
        REFERENCES public.stockinout10(stock_inbound_no),
    purchase_order_no BIGINT NOT NULL,
    receivable_date DATE NOT NULL,
    hq_corp_id TEXT NOT NULL REFERENCES public.companies(corp_id),
    branch_corp_id TEXT NOT NULL REFERENCES public.companies(corp_id),
    total_amount NUMERIC(18, 2) NOT NULL CHECK (total_amount > 0),
    payment_status VARCHAR(1) NOT NULL DEFAULT '0'
        CHECK (payment_status IN ('0', '1')),
    recognition_slip_no BIGINT NOT NULL,
    settled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT ck_franchise_receivable_companies
        CHECK (hq_corp_id <> branch_corp_id),
    CONSTRAINT ck_franchise_receivable_payment_state CHECK (
        (payment_status = '0' AND settled_at IS NULL)
        OR (payment_status = '1' AND settled_at IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_franchise_receivable_hq_date
    ON public.franchise_receivable10(hq_corp_id, receivable_date DESC);
CREATE INDEX IF NOT EXISTS idx_franchise_receivable_branch_date
    ON public.franchise_receivable10(branch_corp_id, receivable_date DESC);

ALTER TABLE public.franchise_receivable10 ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.franchise_receivable10 FROM PUBLIC, anon, authenticated;
GRANT ALL ON public.franchise_receivable10 TO service_role;

CREATE OR REPLACE FUNCTION public.fn_process_purchase_receipt(
    p_po_no BIGINT,
    p_corp_id TEXT,
    p_user_id TEXT DEFAULT 'System'
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE
    v_master public.purchaseorder10%ROWTYPE;
    v_now TIMESTAMPTZ := clock_timestamp();
    v_target_date DATE := (v_now AT TIME ZONE 'Asia/Seoul')::DATE;
    v_prefix TEXT := to_char(v_now AT TIME ZONE 'Asia/Seoul', 'YYYYMMDD');
    v_delivery_date DATE;
    v_io_date_type TEXT;
    v_delivery_date_type TEXT;
    v_io_date_value TEXT;
    v_delivery_date_value TEXT;
    v_is_closed BOOLEAN := FALSE;
    v_stock_inbound_no BIGINT;
    v_slip_no BIGINT;
    v_hq_slip_no BIGINT;
    v_slip_date public.accounting10.slip_date%TYPE;
    v_detail RECORD;
    v_detail_count INTEGER := 0;
    v_net_price NUMERIC(18, 2) := 0;
    v_vat NUMERIC(18, 2) := 0;
    v_total_amount NUMERIC(18, 2) := 0;
BEGIN
    v_slip_date := v_target_date;
    IF p_po_no IS NULL OR p_po_no <= 0 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = '유효한 발주번호가 필요합니다.';
    END IF;
    IF NULLIF(btrim(p_corp_id), '') IS NULL THEN
        RAISE EXCEPTION USING ERRCODE = '28000', MESSAGE = '유효한 회사 인증 정보가 필요합니다.';
    END IF;
    IF to_regprocedure('public.fn_update_stock_atomic(text,text,numeric,boolean)') IS NULL THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'fn_update_stock_atomic 함수를 먼저 설치해야 합니다.';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM public.companies AS company
         WHERE company.corp_id = btrim(p_corp_id)
           AND company.corp_category = '20'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = '가맹점 회사만 입고를 확정할 수 있습니다.';
    END IF;

    SELECT po.* INTO v_master
      FROM public.purchaseorder10 AS po
     WHERE po.purchase_order_no = p_po_no
       AND po.corp_id = btrim(p_corp_id)
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = '발주서를 찾을 수 없습니다.';
    END IF;
    IF COALESCE(v_master.order_status, '') <> '40' THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = '배송중 상태의 발주만 입고 확정할 수 있습니다.';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM public.companies AS company
         WHERE company.corp_id = v_master.partner_id
           AND company.corp_category = '10'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = '본사에서 배송한 가맹점 발주만 입고 확정할 수 있습니다.';
    END IF;
    IF EXISTS (
        SELECT 1 FROM public.stockinout10 AS stock_master
         WHERE stock_master.purchase_order_no = p_po_no
           AND stock_master.corp_id = btrim(p_corp_id)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = '이미 입고 전표가 생성된 발주입니다.';
    END IF;

    PERFORM public.fn_assert_books_open(btrim(p_corp_id), v_target_date);
    PERFORM public.fn_assert_books_open(v_master.partner_id, v_target_date);

    IF to_regclass('public.closing_history') IS NOT NULL THEN
        EXECUTE '
            SELECT EXISTS (
                SELECT 1 FROM public.closing_history AS closing
                 WHERE closing.corp_id::TEXT = $1
                   AND closing.closing_date::TEXT = $2
                   AND closing.is_closed IS TRUE
            )
        '
        INTO v_is_closed
        USING btrim(p_corp_id), v_target_date::TEXT;

        IF v_is_closed THEN
            RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = '오늘 날짜가 이미 마감되어 입고를 확정할 수 없습니다.';
        END IF;
    END IF;

    SELECT
        COUNT(*),
        COALESCE(SUM(COALESCE(detail.net_price, 0)), 0),
        COALESCE(SUM(COALESCE(detail.vat, 0)), 0),
        COALESCE(SUM(COALESCE(detail.total_amount, 0)), 0)
      INTO v_detail_count, v_net_price, v_vat, v_total_amount
      FROM public.purchaseorder20 AS detail
     WHERE detail.purchase_order_no = p_po_no;

    IF v_detail_count = 0 THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = '입고 확정할 발주 품목이 없습니다.';
    END IF;
    IF EXISTS (
        SELECT 1 FROM public.purchaseorder20 AS detail
         WHERE detail.purchase_order_no = p_po_no
           AND (NULLIF(btrim(detail.prod_code), '') IS NULL OR COALESCE(detail.qty, 0) <= 0)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = '입고 품목의 상품코드와 수량은 유효해야 합니다.';
    END IF;

    IF NULLIF(btrim(v_master.delivery_date::TEXT), '') IS NOT NULL THEN
        v_delivery_date := (
            v_master.delivery_date::TEXT::TIMESTAMPTZ AT TIME ZONE 'Asia/Seoul'
        )::DATE;
    END IF;

    SELECT column_info.data_type
      INTO v_io_date_type
      FROM information_schema.columns AS column_info
     WHERE column_info.table_schema = 'public'
       AND column_info.table_name = 'stockinout10'
       AND column_info.column_name = 'io_date';
    SELECT column_info.data_type
      INTO v_delivery_date_type
      FROM information_schema.columns AS column_info
     WHERE column_info.table_schema = 'public'
       AND column_info.table_name = 'stockinout10'
       AND column_info.column_name = 'delivery_date';

    v_io_date_value := CASE v_io_date_type
        WHEN 'timestamp with time zone' THEN v_target_date::TEXT || 'T00:00:00+09:00'
        WHEN 'timestamp without time zone' THEN v_target_date::TEXT || ' 00:00:00'
        ELSE v_target_date::TEXT
    END;
    IF v_delivery_date IS NOT NULL THEN
        v_delivery_date_value := CASE v_delivery_date_type
            WHEN 'timestamp with time zone' THEN v_delivery_date::TEXT || 'T00:00:00+09:00'
            WHEN 'timestamp without time zone' THEN v_delivery_date::TEXT || ' 00:00:00'
            ELSE v_delivery_date::TEXT
        END;
    END IF;

    SELECT public.get_next_no('stockinout10', 'stock_inbound_no', v_prefix)
      INTO v_stock_inbound_no;

    -- jsonb_populate_record는 VARCHAR/DATE/TIMESTAMPTZ 이력이 섞인 설치 DB에서
    -- 문자열 날짜를 대상 컬럼의 실제 타입으로 변환한다.
    INSERT INTO public.stockinout10 (
        stock_inbound_no, corp_id, io_type, io_date, purchase_order_no,
        partner_id, dept_code, delivery_date, net_price, vat, total_amount,
        document_status, remark, create_date, update_date
    )
    SELECT
        converted.stock_inbound_no, converted.corp_id, converted.io_type,
        converted.io_date, converted.purchase_order_no, converted.partner_id,
        converted.dept_code, converted.delivery_date, converted.net_price,
        converted.vat, converted.total_amount, converted.document_status,
        converted.remark, converted.create_date, converted.update_date
      FROM jsonb_populate_record(
          NULL::public.stockinout10,
          jsonb_build_object(
              'stock_inbound_no', v_stock_inbound_no,
              'corp_id', btrim(p_corp_id),
              'io_type', '1',
              'io_date', v_io_date_value,
              'purchase_order_no', p_po_no,
              'partner_id', v_master.partner_id,
              'dept_code', v_master.dept_code,
              'delivery_date', v_delivery_date_value,
              'net_price', v_net_price,
              'vat', v_vat,
              'total_amount', v_total_amount,
              'document_status', 'CONFIRMED',
              'remark', '가맹점 발주 입고확정 자동 생성',
              'create_date', v_now,
              'update_date', v_now
          )
      ) AS converted;

    FOR v_detail IN
        SELECT id, prod_code, prod_type_code, spec, unit, qty, unit_price,
               net_price, vat, total_amount
          FROM public.purchaseorder20
         WHERE purchase_order_no = p_po_no
         ORDER BY id
    LOOP
        INSERT INTO public.stockinout20 (
            stock_inbound_no, corp_id, prod_code, prod_type_code, spec, unit,
            qty, unit_price, net_price, vat, total_amount, create_date, update_date
        ) VALUES (
            v_stock_inbound_no, btrim(p_corp_id), v_detail.prod_code,
            v_detail.prod_type_code, v_detail.spec, v_detail.unit,
            v_detail.qty, v_detail.unit_price, v_detail.net_price,
            v_detail.vat, v_detail.total_amount, v_now, v_now
        );

        PERFORM public.fn_update_stock_atomic(
            btrim(p_corp_id), v_detail.prod_code, v_detail.qty, FALSE
        );
    END LOOP;

    SELECT public.get_next_no('accounting10', 'slip_no', v_prefix)
      INTO v_slip_no;

    INSERT INTO public.accounting10 (
        slip_no, slip_date, corp_id, partner_id, account_code,
        debit_amt, credit_amt, remark, purchase_order_no, stock_inbound_no,
        line_no, source_type, create_date
    ) VALUES (
        v_slip_no, v_slip_date, btrim(p_corp_id), v_master.partner_id, '146',
        v_net_price, 0, format('주문번호 %s 입고 확정에 따른 상품 매입', p_po_no),
        p_po_no, v_stock_inbound_no, 1, 'PURCHASE_RECEIPT', v_now
    );

    -- 같은 입고확정 사건에서 본사의 외상매출금도 함께 인식한다.
    SELECT public.get_next_no('accounting10', 'slip_no', v_prefix)
      INTO v_hq_slip_no;

    INSERT INTO public.accounting10 (
        slip_no, slip_date, corp_id, partner_id, account_code,
        debit_amt, credit_amt, remark, purchase_order_no, stock_inbound_no,
        line_no, source_type, create_date
    ) VALUES
    (
        v_hq_slip_no, v_slip_date, v_master.partner_id,
        btrim(p_corp_id), '108', v_total_amount, 0,
        format('주문번호 %s 가맹점 외상매출금 인식', p_po_no),
        p_po_no, v_stock_inbound_no, 1, 'FRANCHISE_RECEIVABLE', v_now
    ),
    (
        v_hq_slip_no, v_slip_date, v_master.partner_id,
        btrim(p_corp_id), '401', 0, v_total_amount,
        format('주문번호 %s 가맹점 상품매출 인식', p_po_no),
        p_po_no, v_stock_inbound_no, 2, 'FRANCHISE_RECEIVABLE', v_now
    );

    UPDATE public.companies AS branch
       SET current_balance = COALESCE(branch.current_balance, 0) + v_total_amount,
           update_date = v_now
     WHERE branch.corp_id = btrim(p_corp_id)
       AND branch.corp_category = '20';

    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = '가맹점 잔액을 인식할 회사를 찾을 수 없습니다.';
    END IF;

    INSERT INTO public.franchise_receivable10 (
        stock_inbound_no, purchase_order_no, receivable_date,
        hq_corp_id, branch_corp_id, total_amount, recognition_slip_no
    ) VALUES (
        v_stock_inbound_no, p_po_no, v_target_date,
        v_master.partner_id, btrim(p_corp_id), v_total_amount, v_hq_slip_no
    );

    IF v_vat > 0 THEN
        INSERT INTO public.accounting10 (
            slip_no, slip_date, corp_id, partner_id, account_code,
            debit_amt, credit_amt, remark, purchase_order_no, stock_inbound_no,
            line_no, source_type, create_date
        ) VALUES (
            v_slip_no, v_slip_date, btrim(p_corp_id), v_master.partner_id, '135',
            v_vat, 0, format('주문번호 %s 매입 부가세', p_po_no),
            p_po_no, v_stock_inbound_no, 2, 'PURCHASE_RECEIPT', v_now
        );
    END IF;

    INSERT INTO public.accounting10 (
        slip_no, slip_date, corp_id, partner_id, account_code,
        debit_amt, credit_amt, remark, purchase_order_no, stock_inbound_no,
        line_no, source_type, create_date
    ) VALUES (
        v_slip_no, v_slip_date, btrim(p_corp_id), v_master.partner_id, '251',
        0, v_total_amount, format('주문번호 %s 상품 매입 외상 대금', p_po_no),
        p_po_no, v_stock_inbound_no, CASE WHEN v_vat > 0 THEN 3 ELSE 2 END,
        'PURCHASE_RECEIPT', v_now
    );

    UPDATE public.purchaseorder10 AS po
       SET order_status = '60', update_date = v_now
     WHERE po.purchase_order_no = v_master.purchase_order_no
       AND po.corp_id = v_master.corp_id
       AND po.order_status = '40';

    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = '발주서 상태가 변경되어 입고를 확정할 수 없습니다.';
    END IF;

    INSERT INTO public.audit_logs (
        corp_id, table_name, record_id, action,
        old_values, new_values, user_id, reason
    ) VALUES (
        btrim(p_corp_id), 'purchaseorder10', p_po_no::TEXT, 'UPDATE',
        jsonb_build_object('order_status', '40'),
        jsonb_build_object(
            'order_status', '60',
            'stock_inbound_no', v_stock_inbound_no,
            'accounting_slip_no', v_slip_no,
            'hq_receivable_slip_no', v_hq_slip_no,
            'receivable_amount', v_total_amount
        ),
        COALESCE(NULLIF(btrim(p_user_id), ''), 'System'),
        format('가맹점 발주 입고확정: 입고번호 %s', v_stock_inbound_no)
    );

    RETURN jsonb_build_object(
        'status', 'success',
        'sio_no', v_stock_inbound_no,
        'slip_no', v_slip_no,
        'po_no', p_po_no,
        'data', jsonb_build_object(
            'purchase_order_no', p_po_no,
            'stock_inbound_no', v_stock_inbound_no,
            'accounting_slip_no', v_slip_no,
            'hq_receivable_slip_no', v_hq_slip_no,
            'order_status', '60',
            'item_count', v_detail_count,
            'net_price', v_net_price,
            'vat', v_vat,
            'total_amount', v_total_amount,
            'update_date', v_now
        )
    );
END;
$function$;

REVOKE ALL ON FUNCTION public.fn_process_purchase_receipt(BIGINT, TEXT, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.fn_process_purchase_receipt(BIGINT, TEXT, TEXT) FROM authenticated;
REVOKE ALL ON FUNCTION public.fn_process_purchase_receipt(BIGINT, TEXT, TEXT) FROM anon;
GRANT EXECUTE ON FUNCTION public.fn_process_purchase_receipt(BIGINT, TEXT, TEXT) TO service_role;

COMMENT ON FUNCTION public.fn_process_purchase_receipt(BIGINT, TEXT, TEXT)
IS '배송중 가맹점 발주의 입고·재고·양사 회계·매출채권·가맹점 잔액·감사를 한 트랜잭션으로 저장한다. service_role 전용.';

NOTIFY pgrst, 'reload schema';

COMMIT;
