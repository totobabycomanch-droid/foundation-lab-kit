-- 1. 테이블 생성 (의존성 순서 준수)
CREATE TABLE stock (
    product_id VARCHAR(50) PRIMARY KEY,
    quantity INT NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    -- [주니어 팁] 회사 소속을 기록하는 필드입니다. 이 컬럼만으로 접근을 제한하지는 않습니다.
    -- Day 프로젝트와 2권에서 DB RLS(행 단위 보안) 정책을 이해하는 주춧돌이 됩니다. (자세한 흐름은 11.13절 참고)
    corp_id VARCHAR(50) NOT NULL DEFAULT 'HQ'
);

CREATE TABLE orders (
    order_id UUID PRIMARY KEY,
    product_id VARCHAR(50) REFERENCES stock(product_id),
    quantity INT NOT NULL CHECK (quantity > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'CREATED'
        CHECK (status IN ('CREATED', 'PAID')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- [주니어 팁] 회사 소속 식별자이며, 이 실습에는 RLS 정책을 추가하지 않습니다.
    corp_id VARCHAR(50) NOT NULL DEFAULT 'HQ'
);

CREATE TABLE stock_ledger (
    ledger_id BIGSERIAL PRIMARY KEY,
    product_id VARCHAR(50) REFERENCES stock(product_id),
    qty_change INT NOT NULL,
    reason VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- [주니어 팁] 회사 소속 식별자이며, 이 실습에는 RLS 정책을 추가하지 않습니다.
    corp_id VARCHAR(50) NOT NULL DEFAULT 'HQ'
);

-- 2. 주문 승인 트랜잭션 함수 생성
CREATE OR REPLACE FUNCTION approve_order(
    p_order_id UUID,
    p_product_id VARCHAR(50),
    p_qty INT
) RETURNS VOID AS $$
DECLARE
    v_current_stock INT;
    v_order_product_id VARCHAR(50);
    v_order_qty INT;
BEGIN
    -- API를 거치지 않고 함수를 호출해도 잘못된 수량을 거절합니다.
    IF p_qty IS NULL OR p_qty <= 0 THEN
        RAISE EXCEPTION '승인 수량은 1 이상이어야 합니다.';
    END IF;

    -- 처리 중 주문 내용이 바뀌지 않도록 잠그고, 저장된 상품·수량과 대조합니다.
    SELECT product_id, quantity INTO v_order_product_id, v_order_qty
    FROM orders
    WHERE order_id = p_order_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION '주문 정보가 존재하지 않습니다.';
    END IF;

    IF v_order_product_id IS DISTINCT FROM p_product_id
       OR v_order_qty IS DISTINCT FROM p_qty THEN
        RAISE EXCEPTION '요청 상품 또는 수량이 저장된 주문과 다릅니다.';
    END IF;

    -- 같은 상품의 재고를 바꾸는 요청은 이 행의 잠금을 얻을 때까지 기다립니다.
    SELECT quantity INTO v_current_stock
    FROM stock
    WHERE product_id = p_product_id
    FOR UPDATE;

    IF v_current_stock IS NULL THEN
        RAISE EXCEPTION '상품 정보가 존재하지 않습니다.';
    END IF;

    IF v_current_stock < p_qty THEN
        RAISE EXCEPTION '재고가 부족합니다. (현재 재고: %, 요청 수량: %)',
            v_current_stock, p_qty;
    END IF;

    -- 원자적 상태 변경 처리
    UPDATE stock 
    SET quantity = quantity - p_qty 
    WHERE product_id = p_product_id;

    INSERT INTO stock_ledger (product_id, qty_change, reason) 
    VALUES (
        p_product_id, 
        -p_qty, 
        '주문 승인 처리 (' || p_order_id || ')'
    );

    UPDATE orders 
    SET status = 'PAID' 
    WHERE order_id = p_order_id;
END;
$$ LANGUAGE plpgsql;
