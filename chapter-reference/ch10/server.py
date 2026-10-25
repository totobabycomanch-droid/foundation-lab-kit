# server.py
from contextlib import closing
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uuid
from db import get_connection

app = FastAPI()

class OrderItem(BaseModel):
    product_id: str
    quantity: int

class OrderRequest(BaseModel):
    corp_id: str
    items: List[OrderItem]

@app.post("/orders")
def create_order(req: OrderRequest):
    order_id = str(uuid.uuid4())
    conn = get_connection()
    try:
        # DBAPI2 표준 커서를 통해 SQL 작업 수행
        with closing(conn.cursor()) as cur:
            # 1단계. 주문 마스터 생성 (요청으로 받은 회사 ID 저장)
            cur.execute(
                "INSERT INTO orders (order_id, corp_id, order_status) "
                "VALUES (%s, %s, 'CREATED')",
                (order_id, req.corp_id)
            )

            for item in req.items:
                # 2-1단계. DB에서 현재 유효한 상품 단가 조회
                # [주니어 독해 팁] 아래 WHERE 조건은 "현재 유효한 최신 가격"을 찾습니다.
                # - valid_from <= NOW(): 가격 시작일이 현재보다 이전이고,
                # - valid_to IS NULL: 종료일이 없거나(현재 진행형),
                # - valid_to >= NOW(): 종료일이 아직 오지 않은 경우
                cur.execute(
                    "SELECT price FROM product_prices "
                    "WHERE product_id = %s "
                    "AND valid_from <= NOW() "
                    "AND (valid_to IS NULL OR valid_to >= NOW()) "
                    "ORDER BY valid_from DESC LIMIT 1",
                    (item.product_id,)
                )
                price_row = cur.fetchone()
                if not price_row:
                    raise HTTPException(
                        status_code=400,
                        detail=f"상품 가격 정보를 찾을 수 없습니다: {item.product_id}"
                    )
                price_snapshot = price_row[0]

                # 2-1단계. 주문 상세에 주문 당시 단가 저장
                cur.execute(
                    "INSERT INTO order_items "
                    "(order_id, product_id, quantity, price_snapshot) "
                    "VALUES (%s, %s, %s, %s)",
                    (order_id, item.product_id, item.quantity, price_snapshot)
                )
                
                # 2-2단계. 현재 재고 가용성 확인
                # 단일 요청의 부족 여부만 확인합니다.
                # 단일 DB에서도 동시 요청은 같은 재고를 읽을 수 있습니다.
                cur.execute(
                    "SELECT COALESCE(SUM(quantity_change), 0) FROM stock_ledger "
                    "WHERE product_id = %s",
                    (item.product_id,)
                )
                current_stock = cur.fetchone()[0]
                if current_stock < item.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"재고 부족. 현재 재고: {current_stock}, 요청 수량: {item.quantity}"
                    )

                # 2-3단계. 재고 Ledger 기록 (수불부 기반 차감)
                cur.execute(
                    "INSERT INTO stock_ledger "
                    "(product_id, quantity_change) VALUES (%s, %s)",
                    (item.product_id, -item.quantity)
                )

            # 3단계. 비즈니스 이벤트 기록 (외부 전송은 구현하지 않음)
            cur.execute(
                "INSERT INTO order_events "
                "(event_id, order_id, event_type) "
                "VALUES (%s, %s, 'OrderCreated')",
                (str(uuid.uuid4()), order_id)
            )

            # 3단계. 주문 상태 이력 기록 (order_state_history)
            # 초기 상태 기록. 이력의 수정·삭제 차단은 별도 구현이 필요합니다.
            # Day 프로젝트의 발주 변경은 별도 스키마와 감사 기록을 사용합니다.
            cur.execute(
                "INSERT INTO order_state_history "
                "(order_id, from_status, to_status) "
                "VALUES (%s, %s, %s)",
                (order_id, None, 'CREATED')
            )

        # 4단계. COMMIT (모든 단계 성공 시 저장 확정)
        conn.commit()
        return {"status": "success", "order_id": order_id}

    except HTTPException:
        # 가격 없음·재고 부족 같은 업무 오류: 롤백 후 400 응답을 그대로 전달
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback() # 예외 발생 시 트랜잭션 전체 롤백 (All-or-Nothing 보장)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
