# 파일 경로: project/tests/test_change.py
# 요청 검증만 DB 없이 검사합니다
from dataclasses import FrozenInstanceError

import pytest

from services.franchise_order import (
    FranchiseOrderChangeError,
    FranchiseOrderEvent,
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
