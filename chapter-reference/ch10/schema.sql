-- 기존 테이블이 존재할 경우 삭제 (외래 키 참조 관계를 고려하여 역순/CASCADE 삭제)
DROP TABLE IF EXISTS order_state_history CASCADE;
DROP TABLE IF EXISTS order_events CASCADE;
DROP TABLE IF EXISTS stock_ledger CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS product_prices CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS companies CASCADE;

-- 1. COMPANIES (주문이 참조하는 회사 기준정보)
CREATE TABLE companies (
    corp_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    corp_name TEXT NOT NULL
);

-- 2. PRODUCTS (상품 기준 정보)
CREATE TABLE products (
    product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_name TEXT NOT NULL
);

-- 3. PRODUCT_PRICES (상품 가격 변천사 이력)
CREATE TABLE product_prices (
    product_price_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    price NUMERIC NOT NULL CHECK (price >= 0),
    valid_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 이 가격의 시작일 (예: 2024-01-01부터 5,000원)
    valid_to TIMESTAMP  -- 이 가격의 종료일 (NULL이면 현재도 유효한 최신 가격)
);

-- 4. ORDERS (소속 회사와 현재 상태를 저장하는 주문 마스터)
CREATE TABLE orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    corp_id UUID NOT NULL REFERENCES companies(corp_id) ON DELETE RESTRICT,
    order_status TEXT NOT NULL CHECK (order_status IN ('CREATED', 'PAID', 'CANCELLED', 'SHIPPED')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- 회사별 주문 ID 조회를 돕는 인덱스. 권한 검사나 생성시각 정렬을 보장하지 않음
CREATE INDEX idx_orders_corp_order ON orders (corp_id, order_id);

-- 5. ORDER_ITEMS (주문 상세 품목 및 가격 스냅샷)
CREATE TABLE order_items (
    order_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
    quantity INT NOT NULL CHECK (quantity > 0),
    price_snapshot NUMERIC NOT NULL CHECK (price_snapshot >= 0)
);

-- 6. STOCK_LEDGER (상품별 재고 증감 기록)
CREATE TABLE stock_ledger (
    ledger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
    quantity_change INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 학습 범위: 증감 기록과 단일 요청의 롤백을 체험합니다.
-- 동시 출고 제어와 원장 UPDATE·DELETE 차단은 구현하지 않습니다.
-- SUM 검사만 하는 트리거도 동시 출고 안전성을 보장하지 않습니다.

-- 7. ORDER_EVENTS (비즈니스 이벤트 로그)
CREATE TABLE order_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'OrderCreated', 'OrderCancelled', 'OrderPaid',
        'OrderShipped', 'OrderDelivered'
    )),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 8. ORDER_STATE_HISTORY (주문 상태 변경 이력)
CREATE TABLE order_state_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    from_status TEXT,
    to_status TEXT NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
