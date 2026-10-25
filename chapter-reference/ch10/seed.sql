-- 1. 테스트용 가맹점(Company) 데이터 삽입
INSERT INTO companies (corp_id, corp_name) 
VALUES (
    '11111111-1111-1111-1111-111111111111', 
    '테스트 가맹점 A'
)
ON CONFLICT (corp_id) DO NOTHING;

-- 2. 테스트용 상품(Product) 데이터 삽입
INSERT INTO products (product_id, product_name) 
VALUES 
    (
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 
        '신라면 5입 팩'
    ),
    (
        'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 
        '코카콜라 250ml'
    ),
    -- 가격을 일부러 등록하지 않는 검증용 상품 (Core 완료 후 선택 실습의 가격 없음 거절 확인용)
    (
        'dddddddd-dddd-dddd-dddd-dddddddddddd',
        '가격 없음 검증용 상품'
    )
ON CONFLICT (product_id) DO NOTHING;

-- 3. 테스트용 상품 가격(Product Price) 데이터 삽입
INSERT INTO product_prices (
    product_price_id, product_id, price, valid_from
) 
VALUES 
    (
        '11111111-2222-3333-4444-555555555555', 
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 
        5000, 
        CURRENT_TIMESTAMP
    ),
    (
        '66666666-7777-8888-9999-000000000000', 
        'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 
        12000, 
        CURRENT_TIMESTAMP
    )
ON CONFLICT (product_price_id) DO NOTHING;

-- 4. 테스트용 초기 입고: 신라면·코카콜라 각 100개, 가격 없음 검증용 상품 10개
-- 고정 ledger_id로 같은 준비 SQL을 재실행해도 입고가 중복되지 않게 합니다.
INSERT INTO stock_ledger (ledger_id, product_id, quantity_change)
VALUES
    ('cccccccc-cccc-cccc-cccc-ccccccccccc1',
     'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 100),
    ('cccccccc-cccc-cccc-cccc-ccccccccccc2',
     'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 100),
    ('cccccccc-cccc-cccc-cccc-ccccccccccc3',
     'dddddddd-dddd-dddd-dddd-dddddddddddd', 10)
ON CONFLICT (ledger_id) DO NOTHING;
