from fastapi import APIRouter, Depends, HTTPException, Request

from .lab_auth import LabUser, current_lab_user

router = APIRouter(prefix="/api/lab")


@router.get("/orders/{order_id}")
def read_company_order(order_id: int, request: Request, user: LabUser = Depends(current_lab_user)) -> dict:
    # 회사별 조회 실습에서 AI가 구현합니다. 세션과 조회용 발주는 준비되어 있습니다.
    raise HTTPException(status_code=501, detail="회사별 발주 조회를 구현해 주세요.")
