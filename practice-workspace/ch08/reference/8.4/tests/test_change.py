# 파일 경로: project/tests/test_change.py
# 요청 검증과 업무 판단을 DB 없이 검사합니다
from dataclasses import FrozenInstanceError

import pytest

from services.franchise_order import (
    FranchiseOrderChangeError,
    FranchiseOrderEvent,
    decide_franchise_order,
    parse_franchise_order_event,
)


def event(qty=5):
    return FranchiseOrderEvent(franchise_id=1, prod_code="A001", qty=qty)


def test_parse_accepts_valid_payload():
    parsed = parse_franchise_order_event({"franchise_id": 1, "prod_code": " A001 ", "qty": 5})
    assert parsed == FranchiseOrderEvent(franchise_id=1, prod_code="A001", qty=5)


@pytest.mark.parametrize("payload, code", [
    ({"franchise_id": 1, "prod_code": "A001", "qty": 0}, "invalid_qty"),
    ({"franchise_id": 1, "prod_code": "A001", "qty": -1}, "invalid_qty"),
    ({"franchise_id": 1, "prod_code": "A001", "qty": "5"}, "invalid_qty"),
    ({"franchise_id": 1, "prod_code": "A001", "qty": True}, "invalid_qty"),
    ({"franchise_id": 1, "prod_code": "A001"}, "invalid_qty"),
    ({"franchise_id": 1, "prod_code": "  ", "qty": 5}, "invalid_prod_code"),
    ({"franchise_id": 0, "prod_code": "A001", "qty": 5}, "invalid_franchise_id"),
    (None, "invalid_payload"),
])
def test_parse_rejects_invalid_payload(payload, code):
    with pytest.raises(FranchiseOrderChangeError) as caught:
        parse_franchise_order_event(payload)
    assert caught.value.code == code


def test_event_is_immutable():
    with pytest.raises(FrozenInstanceError):
        event().qty = 99


def test_decide_normal_order():
    plan = decide_franchise_order(event(), stock_qty=100, unit_price=1000, deposit=50000)
    assert (plan.qty, plan.total_price, plan.order_status) == (5, 5000, 10)


@pytest.mark.parametrize("stock_qty, deposit", [
    (5, 50000),   # 재고가 요청 수량과 같음
    (100, 5000),  # 예치금이 주문 금액과 같음
    (5, 5000),    # 두 경계가 동시에 같음
])
def test_decide_allows_exact_boundaries(stock_qty, deposit):
    plan = decide_franchise_order(event(), stock_qty=stock_qty, unit_price=1000, deposit=deposit)
    assert plan.total_price == 5000


@pytest.mark.parametrize("qty, stock_qty, deposit, code", [
    (15, 10, 20000, "insufficient_stock"),
    (5, 100, 4999, "insufficient_deposit"),
])
def test_decide_rejects_shortage(qty, stock_qty, deposit, code):
    with pytest.raises(FranchiseOrderChangeError) as caught:
        decide_franchise_order(event(qty), stock_qty=stock_qty, unit_price=1000, deposit=deposit)
    assert caught.value.code == code


def test_decide_prioritizes_stock_when_both_are_short():
    with pytest.raises(FranchiseOrderChangeError) as caught:
        decide_franchise_order(event(), stock_qty=4, unit_price=1000, deposit=4999)
    assert caught.value.code == "insufficient_stock"
