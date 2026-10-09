# 파일 경로: project/routers/franchise_order.py
# HTTP 요청을 받아 요청 검증·상품 조회·업무 판단·저장을 연결합니다

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import Product
from repositories.franchise_order import persist_franchise_order
from services.franchise_order import (
    CHANGE_ERROR_HTTP_STATUS,
    FranchiseOrderChangeError,
    ProductSnapshot,
    decide_franchise_order,
    parse_franchise_order_event,
)

router = APIRouter()


@router.post("/franchise/order")
def create_franchise_order(payload: dict, db: Session = Depends(get_db)):
    try:
        order_event = parse_franchise_order_event(payload)
        product_codes = [item.prod_code for item in order_event.details]

        with db.begin():
            rows = db.scalars(
                select(Product).where(Product.prod_code.in_(product_codes))
            ).all()
            products = {
                row.prod_code: ProductSnapshot(
                    prod_code=row.prod_code,
                    unit_price=row.unit_price,
                    is_active=row.is_active,
                )
                for row in rows
            }

        plan = decide_franchise_order(order_event, products=products)
        purchase_order_no = persist_franchise_order(plan, db)
    except FranchiseOrderChangeError as exc:
        raise HTTPException(
            status_code=CHANGE_ERROR_HTTP_STATUS[exc.code], detail=str(exc)
        ) from exc
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409, detail="다른 요청과 충돌하여 발주를 저장하지 못했습니다."
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="발주 저장 중 서버 오류가 발생했습니다."
        ) from exc

    return {
        "status": "success",
        "purchase_order_no": purchase_order_no,
        "order_status": plan.order_status,
        "detail_count": len(plan.details),
        "total_amount": plan.total_amount,
    }
