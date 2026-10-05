# 파일 경로: project/services/franchise_order.py
# 요청 검증과 업무 판단: DB 없이 값을 다룹니다

from dataclasses import dataclass
from typing import Any, Mapping




class FranchiseOrderChangeError(ValueError):
    """DB를 읽기 전후의 순수 단계에서 발견한 업무 규칙 위반."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class FranchiseOrderEvent:
    """가맹점이 발주하려는 의도. 타입과 공백만 정리한 불변 값입니다."""

    franchise_id: int
    prod_code: str
    qty: int




def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def parse_franchise_order_event(payload: Mapping[str, Any]) -> FranchiseOrderEvent:
    """요청 본문을 DB 접근 없이 검증하고 Event로 만든다."""

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
