-- 새 ch11 전용 실습 DB에만 적용합니다. 기존 테이블을 삭제하거나 이전하지 않습니다.
CREATE TABLE public.stock (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    quantity INT NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    corp_id VARCHAR(50) NOT NULL DEFAULT 'HQ'
);

CREATE TABLE public.orders (
    order_id UUID PRIMARY KEY,
    order_name VARCHAR(100) NOT NULL,
    product_id VARCHAR(50) NOT NULL REFERENCES public.stock(product_id),
    quantity INT NOT NULL CHECK (quantity > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'CREATED' CHECK (status IN ('CREATED', 'PAID')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    corp_id VARCHAR(50) NOT NULL DEFAULT 'HQ'
);

CREATE TABLE public.stock_ledger (
    ledger_id BIGSERIAL PRIMARY KEY,
    order_id UUID NOT NULL UNIQUE REFERENCES public.orders(order_id),
    product_id VARCHAR(50) NOT NULL REFERENCES public.stock(product_id),
    qty_change INT NOT NULL,
    reason VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    corp_id VARCHAR(50) NOT NULL DEFAULT 'HQ'
);

-- 함수의 세 변경은 호출한 API 트랜잭션에서 함께 확정하거나 취소합니다.
CREATE OR REPLACE FUNCTION public.approve_order(
    p_order_id UUID,
    p_product_id VARCHAR(50),
    p_qty INTEGER
) RETURNS VOID
LANGUAGE plpgsql
SET search_path = public, pg_catalog
AS $approve$
DECLARE
    v_order public.orders%ROWTYPE;
    v_stock INTEGER;
BEGIN
    IF p_qty IS NULL OR p_qty <= 0 THEN
        RAISE EXCEPTION USING ERRCODE = 'P1101', MESSAGE = '승인 수량은 1 이상이어야 합니다.';
    END IF;

    SELECT * INTO v_order FROM public.orders
    WHERE order_id = p_order_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P1102', MESSAGE = '주문 정보가 존재하지 않습니다.';
    END IF;
    IF v_order.product_id IS DISTINCT FROM p_product_id
       OR v_order.quantity IS DISTINCT FROM p_qty THEN
        RAISE EXCEPTION USING ERRCODE = 'P1103', MESSAGE = '요청 상품 또는 수량이 저장된 주문과 다릅니다.';
    END IF;
    -- 같은 주문을 기다리던 요청도 잠금 획득 뒤 최신 상태로 판단합니다.
    IF v_order.status <> 'CREATED' THEN
        RAISE EXCEPTION USING ERRCODE = 'P1104', MESSAGE = '이미 승인된 주문입니다.';
    END IF;

    SELECT quantity INTO v_stock FROM public.stock
    WHERE product_id = p_product_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P1105', MESSAGE = '상품 정보가 존재하지 않습니다.';
    END IF;
    IF v_stock < p_qty THEN
        RAISE EXCEPTION USING ERRCODE = 'P1106', MESSAGE = '재고가 부족합니다.';
    END IF;

    UPDATE public.stock SET quantity = quantity - p_qty WHERE product_id = p_product_id;
    INSERT INTO public.stock_ledger(order_id, product_id, qty_change, reason, corp_id)
    VALUES (p_order_id, p_product_id, -p_qty, '주문 승인 처리', v_order.corp_id);
    UPDATE public.orders SET status = 'PAID' WHERE order_id = p_order_id;
END;
$approve$;
