from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.core.database import get_system_db, get_tenant_db
from app.core.idempotency import idempotent
from app.core.security import verify_token
from app.services.closing_adapter import check_closing_guard


router = APIRouter()


def _raise_purchase_receipt_rpc_error(exc: Exception):
    message = getattr(exc, "message", None) or str(exc)
    if getattr(exc, "code", None) == "P0001":
        raise HTTPException(status_code=409, detail=message) from exc
    raise HTTPException(status_code=500, detail="입고 확정 중 서버 오류가 발생했습니다.") from exc


@router.post("/api/v1/purchase_orders/status_store")
@idempotent(require_key=True)
async def update_purchase_order_status_store(
    payload: dict,
    req: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    token: Optional[str] = None,
    db=Depends(get_tenant_db),
):
    """가맹점의 배송중(40) 발주를 입고확정(60)한다."""
    auth_info = await verify_token(token)
    corp_id = auth_info["corp_id"]

    if payload.get("status") != "60":
        raise HTTPException(status_code=403, detail="가맹점은 입고확정 처리만 가능합니다.")
    try:
        purchase_order_no = int(payload.get("purchase_order_no"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="유효한 발주번호가 필요합니다.")

    try:
        await check_closing_guard(db, corp_id, datetime.now(timezone.utc).date().isoformat())
        rpc_response = get_system_db().rpc(
            "fn_process_purchase_receipt",
            {
                "p_po_no": purchase_order_no,
                "p_corp_id": corp_id,
                "p_user_id": str(auth_info.get("user_id") or "System"),
            },
        ).execute()
    except HTTPException:
        raise
    except Exception as exc:
        _raise_purchase_receipt_rpc_error(exc)

    result = rpc_response.data
    if not isinstance(result, dict) or result.get("status") != "success":
        raise HTTPException(status_code=500, detail="입고 확정 결과를 확인할 수 없습니다.")

    response = (
        db.table("purchaseorder10")
        .select("*")
        .eq("purchase_order_no", purchase_order_no)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=500, detail="입고 확정 후 발주 상태를 확인할 수 없습니다.")
    return {"status": "success", "data": response.data[0]}
