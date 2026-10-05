# 파일 경로: project/routers/franchise_order.py
# HTTP 요청을 받아 요청 검증·업무 판단·저장을 연결합니다

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Franchise, Stock
from repositories.franchise_order import FranchiseOrderConflict, persist_franchise_order
from services.franchise_order import (
    CHANGE_ERROR_HTTP_STATUS,
    FranchiseOrderChangeError,
    decide_franchise_order,
    parse_franchise_order_event,
)

router = APIRouter()


@router.post("/franchise/order")
def create_franchise_order(payload: dict, db: Session = Depends(get_db)):
    try:
        event = parse_franchise_order_event(payload)

        with db.begin():  # 현재 값을 읽기만 합니다
            stock = db.get(Stock, event.prod_code)
            if stock is None:
                raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
            franchise = db.get(Franchise, event.franchise_id)
            if franchise is None:
                raise HTTPException(status_code=404, detail="가맹점을 찾을 수 없습니다.")
            current = (stock.stock_qty, stock.unit_price, franchise.deposit)

        plan = decide_franchise_order(
            event, stock_qty=current[0], unit_price=current[1], deposit=current[2]
        )
        persist_franchise_order(plan, db)
    except FranchiseOrderChangeError as exc:
        raise HTTPException(
            status_code=CHANGE_ERROR_HTTP_STATUS[exc.code], detail=str(exc)
        ) from exc
    except FranchiseOrderConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"status": plan.order_status}
