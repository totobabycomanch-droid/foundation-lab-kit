-- 정상 A와 부족 B를 한 번의 조회로 비교합니다. 데이터는 변경하지 않습니다.
SELECT o.order_name,
       s.product_name,
       o.quantity AS order_quantity,
       o.status AS order_status,
       s.quantity AS current_stock,
       COUNT(l.ledger_id) AS ledger_count,
       SUM(l.qty_change) AS qty_change
FROM public.orders o
JOIN public.stock s ON s.product_id = o.product_id
LEFT JOIN public.stock_ledger l ON l.order_id = o.order_id
WHERE o.order_id IN (
    '00000000-0000-0000-0000-000000000001'::UUID,
    '00000000-0000-0000-0000-000000000002'::UUID
)
GROUP BY o.order_id, o.order_name, s.product_name, o.quantity, o.status, s.quantity
ORDER BY o.order_id;
