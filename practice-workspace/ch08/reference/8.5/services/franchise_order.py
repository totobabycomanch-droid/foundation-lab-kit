# 파일 경로: project/services/franchise_order.py
# 요청 검증과 업무 판단: DB 없이 값을 다룹니다

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

ORDER_STATUS_PLACED = "10"
BRANCH_CORP_ID = "branch01"
HQ_CORP_ID = "admin"

CHANGE_ERROR_HTTP_STATUS = MappingProxyType(
    {
        "invalid_payload": 400,
        "invalid_master": 400,
        "invalid_detail": 400,
        "duplicate_product": 400,
        "product_not_found": 400,
        "invalid_unit_price": 409,
    }
)


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


@dataclass(frozen=True)
class ProductSnapshot:
    """서버 조회 값의 복사본: 상품 코드·단가·활성 상태를 담으며 DB 모델이 아니다."""

    prod_code: str
    unit_price: int
    is_active: bool


@dataclass(frozen=True)
class BranchOrderLinePlan:
    """품목 저장 계획: 코드·수량·서버 단가·공급가액·VAT·합계를 담는다."""

    prod_code: str
    qty: int
    unit_price: int
    net_price: int
    vat: int
    total_amount: int


@dataclass(frozen=True)
class BranchOrderPlan:
    """전체 저장 계획: 회사·거래처·요청 기본 정보·상태·합계와 불변 품목 계획을 담는다."""

    corp_id: str
    partner_id: str
    dept_code: str
    emp_code: str
    delivery_code: int
    is_vat: str
    order_status: str
    total_amount: int
    details: tuple[BranchOrderLinePlan, ...]


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


def decide_franchise_order(
    event: BranchOrderEvent,
    *,
    products: Mapping[str, ProductSnapshot],
    actor_corp_id: str = BRANCH_CORP_ID,
) -> BranchOrderPlan:
    """event의 수량과 products의 서버 단가로 불변 BranchOrderPlan을 반환한다.

    actor_corp_id는 서버가 확인한 발주 회사이며 기본값은 branch01이다.
    상품 없음·비활성은 product_not_found, 0 이하 또는 잘못된 단가는 invalid_unit_price다.
    DB 조회·저장은 수행하지 않는다.
    """

    lines: list[BranchOrderLinePlan] = []
    for item in event.details:
        product = products.get(item.prod_code)
        if product is None or not product.is_active:
            raise FranchiseOrderChangeError(
                "product_not_found", f"사용 가능한 상품 {item.prod_code}을(를) 찾을 수 없습니다."
            )
        if not _is_int(product.unit_price) or product.unit_price <= 0:
            raise FranchiseOrderChangeError(
                "invalid_unit_price", f"상품 {item.prod_code}의 유효한 단가가 없습니다."
            )

        net_price = item.qty * product.unit_price
        vat = (net_price + 5) // 10 if event.is_vat == "2" else 0
        lines.append(
            BranchOrderLinePlan(
                prod_code=item.prod_code,
                qty=item.qty,
                unit_price=product.unit_price,
                net_price=net_price,
                vat=vat,
                total_amount=net_price + vat,
            )
        )

    return BranchOrderPlan(
        corp_id=actor_corp_id,
        partner_id=HQ_CORP_ID,
        dept_code=event.dept_code,
        emp_code=event.emp_code,
        delivery_code=event.delivery_code,
        is_vat=event.is_vat,
        order_status=ORDER_STATUS_PLACED,
        total_amount=sum(line.total_amount for line in lines),
        details=tuple(lines),
    )

