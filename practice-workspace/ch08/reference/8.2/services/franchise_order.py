# 파일 경로: project/services/franchise_order.py
# 요청 검증: DB 없이 클라이언트가 결정할 수 있는 값만 다룹니다

from dataclasses import dataclass
from typing import Any, Mapping


class FranchiseOrderChangeError(ValueError):
    """요청 검증이나 업무 판단에서 발견한 규칙 위반."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class BranchOrderItemEvent:
    """요청 품목: prod_code는 상품 코드, qty는 발주 수량이다."""

    prod_code: str
    qty: int


@dataclass(frozen=True)
class BranchOrderEvent:
    """검증한 요청: 부서·사원·배송지·VAT 구분과 불변 품목 목록을 담는다."""

    dept_code: str
    emp_code: str
    delivery_code: int
    is_vat: str
    details: tuple[BranchOrderItemEvent, ...]


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _required_text(value: Any, *, max_length: int, message: str) -> str:
    normalized = value.strip() if isinstance(value, str) else ""
    if not normalized or len(normalized) > max_length:
        raise FranchiseOrderChangeError("invalid_master", message)
    return normalized


def parse_franchise_order_event(payload: Mapping[str, Any]) -> BranchOrderEvent:
    """요청을 검증하고 서버 소유 필드를 제외한 불변 값으로 만든다."""

    if not isinstance(payload, Mapping):
        raise FranchiseOrderChangeError("invalid_payload", "발주 정보가 필요합니다.")

    master = payload.get("master")
    details = payload.get("details")
    if not isinstance(master, Mapping):
        raise FranchiseOrderChangeError("invalid_master", "발주 기본 정보가 필요합니다.")
    if not isinstance(details, list) or not details:
        raise FranchiseOrderChangeError("invalid_detail", "발주 품목은 1건 이상 필요합니다.")

    dept_code = _required_text(
        master.get("dept_code"), max_length=20, message="부서코드가 올바르지 않습니다."
    )
    emp_code = _required_text(
        master.get("emp_code"), max_length=20, message="담당 사원코드가 올바르지 않습니다."
    )

    delivery_code = master.get("delivery_code")
    if not _is_int(delivery_code) or delivery_code <= 0:
        raise FranchiseOrderChangeError("invalid_master", "배송지를 선택해 주세요.")

    raw_is_vat = master["is_vat"] if "is_vat" in master else "1"
    is_vat = raw_is_vat.strip() if isinstance(raw_is_vat, str) else ""
    if is_vat not in {"1", "2"}:
        raise FranchiseOrderChangeError("invalid_master", "부가세 구분이 올바르지 않습니다.")

    normalized_details: list[BranchOrderItemEvent] = []
    seen_codes: set[str] = set()
    for index, detail in enumerate(details, start=1):
        if not isinstance(detail, Mapping):
            raise FranchiseOrderChangeError(
                "invalid_detail", f"{index}번째 발주 품목 형식이 올바르지 않습니다."
            )
        prod_code = detail.get("prod_code")
        prod_code = prod_code.strip() if isinstance(prod_code, str) else ""
        if not prod_code or len(prod_code) > 50:
            raise FranchiseOrderChangeError(
                "invalid_detail", f"{index}번째 품목코드가 올바르지 않습니다."
            )
        if prod_code in seen_codes:
            raise FranchiseOrderChangeError(
                "duplicate_product", "같은 품목코드를 중복해서 입력할 수 없습니다."
            )
        qty = detail.get("qty")
        if not _is_int(qty) or qty <= 0:
            raise FranchiseOrderChangeError(
                "invalid_detail", f"{index}번째 품목 수량은 1 이상이어야 합니다."
            )
        seen_codes.add(prod_code)
        normalized_details.append(BranchOrderItemEvent(prod_code=prod_code, qty=qty))

    return BranchOrderEvent(
        dept_code=dept_code,
        emp_code=emp_code,
        delivery_code=delivery_code,
        is_vat=is_vat,
        details=tuple(normalized_details),
    )
