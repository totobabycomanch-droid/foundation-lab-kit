# 파일 경로: project/repositories/franchise_order.py
# 저장 계획을 한 트랜잭션으로 실행합니다

from sqlalchemy import text
from sqlalchemy.orm import Session

from models import Order
from services.franchise_order import FranchiseOrderPlan


class FranchiseOrderConflict(RuntimeError):
    """저장 시점에 조건이 맞지 않아 전체 저장을 취소한 경우."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def persist_franchise_order(plan: FranchiseOrderPlan, db: Session) -> int:
    """재고 차감, 예치금 차감, 주문 기록을 모두 저장하거나 모두 취소한다."""

    with db.begin():
        stock_update = db.execute(
            text(
                "UPDATE current_stock SET stock_qty = stock_qty - :qty "
                "WHERE prod_code = :code AND stock_qty >= :qty"
            ),
            {"qty": plan.qty, "code": plan.prod_code},
        )
        if stock_update.rowcount != 1:
            raise FranchiseOrderConflict("stock_changed", "재고가 바뀌어 주문을 저장하지 못했습니다.")

        deposit_update = db.execute(
            text(
                "UPDATE franchise SET deposit = deposit - :amount "
                "WHERE id = :f_id AND deposit >= :amount"
            ),
            {"amount": plan.total_price, "f_id": plan.franchise_id},
        )
        if deposit_update.rowcount != 1:
            raise FranchiseOrderConflict("deposit_changed", "예치금이 바뀌어 주문을 저장하지 못했습니다.")

        order = Order(
            franchise_id=plan.franchise_id,
            prod_code=plan.prod_code,
            qty=plan.qty,
            status=plan.order_status,
        )
        db.add(order)
        db.flush()
        return order.id
