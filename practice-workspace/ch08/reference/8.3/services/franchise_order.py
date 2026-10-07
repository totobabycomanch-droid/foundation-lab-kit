# 파일 경로: project/services/franchise_order.py
# 요청 검증과 업무 판단: DB 없이 값을 다룹니다

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

ORDER_STATUS_PLACED = 10  # 10 = 발주완료

CHANGE_ERROR_HTTP_STATUS = MappingProxyType(
    {
        "invalid_payload": 400,
        "invalid_franchise_id": 400,
        "invalid_prod_code": 400,
        "invalid_qty": 400,
        "insufficient_stock": 409,
        "insufficient_deposit": 409,
    }
)


class FranchiseOrderChangeError(ValueError):
    """요청 검증이나 업무 판단에서 발견한 규칙 위반. code로 종류를 구분합니다."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class FranchiseOrderEvent:
    """가맹점이 발주하려는 요청. 타입과 공백만 정리한 불변 값입니다."""

    franchise_id: int
    prod_code: str
    qty: int


@dataclass(frozen=True)
class FranchiseOrderPlan:
    """저장 함수가 그대로 실행할 저장 계획. 최종값이 아니라 줄일 양을 담습니다."""

    franchise_id: int
    prod_code: str
    qty: int
    total_price: int
    order_status: int


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def parse_franchise_order_event(payload: Mapping[str, Any]) -> FranchiseOrderEvent:
    """요청 본문을 DB 접근 없이 검증하고 요청 객체로 만든다."""

    if not isinstance(payload, Mapping):
        raise FranchiseOrderChangeError("invalid_payload", "발주 정보가 필요합니다.")

    franchise_id = payload.get("franchise_id")
    if not _is_int(franchise_id) or franchise_id <= 0:
        raise FranchiseOrderChangeError("invalid_franchise_id", "가맹점 번호가 올바르지 않습니다.")

    raw_code = payload.get("prod_code")
    prod_code = raw_code.strip() if isinstance(raw_code, str) else ""
    if not prod_code:
        raise FranchiseOrderChangeError("invalid_prod_code", "상품 코드가 필요합니다.")

    qty = payload.get("qty")
    if not _is_int(qty) or qty <= 0:
        raise FranchiseOrderChangeError("invalid_qty", "수량은 1 이상이어야 합니다.")

    return FranchiseOrderEvent(franchise_id=franchise_id, prod_code=prod_code, qty=qty)


def decide_franchise_order(
    event: FranchiseOrderEvent,
    *,
    stock_qty: int,
    unit_price: int,
    deposit: int,
) -> FranchiseOrderPlan:
    """현재 재고·단가·예치금으로 주문 가능 여부를 판단하고 저장 계획을 만든다."""

    if stock_qty < event.qty:
        raise FranchiseOrderChangeError(
            "insufficient_stock",
            f"재고가 부족합니다. (현재고: {stock_qty}, 요청수량: {event.qty})",
        )

    total_price = event.qty * unit_price
    if deposit < total_price:
        raise FranchiseOrderChangeError(
            "insufficient_deposit",
            f"예치금이 부족합니다. (예치금: {deposit}, 주문총액: {total_price})",
        )

    return FranchiseOrderPlan(
        franchise_id=event.franchise_id,
        prod_code=event.prod_code,
        qty=event.qty,
        total_price=total_price,
        order_status=ORDER_STATUS_PLACED,
    )
