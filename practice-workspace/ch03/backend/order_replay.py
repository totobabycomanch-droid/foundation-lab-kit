from fastapi import HTTPException

from .models import OrderInput
from .store import LabStore


def save_order_once(store: LabStore, order: OrderInput, request_key: str) -> dict:
    # 서버 재전송 실습에서 AI가 구현합니다. 앞선 정상 저장 실습에서는 호출하지 않습니다.
    raise HTTPException(status_code=501, detail="동일 요청 재전송 처리를 구현해 주세요.")
