from fastapi import APIRouter, HTTPException, Request

from .models import OrderInput

router = APIRouter()


@router.post("/api/orders", status_code=201)
async def create_order(order: OrderInput, request: Request) -> dict:
    # 정상 저장 실습에서 AI가 구현합니다.
    raise HTTPException(status_code=501, detail="발주 저장 기능을 구현해 주세요.")
