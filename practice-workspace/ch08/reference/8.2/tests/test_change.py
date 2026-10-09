# 파일 경로: project/tests/test_change.py
# 요청 검증만 DB 없이 검사합니다
from dataclasses import FrozenInstanceError

import pytest

from services.franchise_order import (
    BranchOrderEvent,
    BranchOrderItemEvent,
    FranchiseOrderChangeError,
    parse_franchise_order_event,
)


def payload():
    return {
        "master": {
            "dept_code": " 10 ",
            "emp_code": " E001 ",
            "delivery_code": 101,
            "is_vat": "2",
        },
        "details": [{"prod_code": " A001 ", "qty": 5}],
    }


def test_parse_accepts_actual_contract_subset_and_discards_server_fields():
    raw = payload()
    raw["master"].update(
        {"corp_id": "tampered", "partner_id": "tampered", "order_status": "60"}
    )
    raw["details"][0].update({"unit_price": 1, "total_amount": 5})

    parsed = parse_franchise_order_event(raw)

    assert parsed == BranchOrderEvent(
        dept_code="10",
        emp_code="E001",
        delivery_code=101,
        is_vat="2",
        details=(BranchOrderItemEvent(prod_code="A001", qty=5),),
    )
    assert not hasattr(parsed, "corp_id")
    assert not hasattr(parsed.details[0], "unit_price")


def test_parse_defaults_omitted_is_vat_to_one():
    raw = payload()
    del raw["master"]["is_vat"]

    assert parse_franchise_order_event(raw).is_vat == "1"


def test_parse_rejects_non_object_payload():
    with pytest.raises(FranchiseOrderChangeError) as caught:
        parse_franchise_order_event([])

    assert caught.value.code == "invalid_payload"


@pytest.mark.parametrize(
    "change, code",
    [
        (lambda value: value.pop("master"), "invalid_master"),
        (lambda value: value.update({"master": None}), "invalid_master"),
        (lambda value: value.pop("details"), "invalid_detail"),
        (lambda value: value.update({"details": None}), "invalid_detail"),
        (lambda value: value.update({"details": []}), "invalid_detail"),
        (lambda value: value["master"].update({"dept_code": ""}), "invalid_master"),
        (lambda value: value["master"].update({"emp_code": 100}), "invalid_master"),
        (lambda value: value["master"].update({"delivery_code": True}), "invalid_master"),
        (lambda value: value["master"].update({"is_vat": None}), "invalid_master"),
        (lambda value: value["master"].update({"is_vat": 2}), "invalid_master"),
        (lambda value: value["master"].update({"is_vat": "3"}), "invalid_master"),
        (lambda value: value["details"][0].update({"prod_code": ""}), "invalid_detail"),
        (lambda value: value["details"][0].update({"qty": 0}), "invalid_detail"),
        (lambda value: value["details"][0].update({"qty": True}), "invalid_detail"),
        (lambda value: value["details"][0].update({"qty": "5"}), "invalid_detail"),
    ],
)
def test_parse_rejects_invalid_payload(change, code):
    raw = payload()
    change(raw)
    with pytest.raises(FranchiseOrderChangeError) as caught:
        parse_franchise_order_event(raw)
    assert caught.value.code == code


def test_parse_rejects_duplicate_product():
    raw = payload()
    raw["details"].append({"prod_code": "A001", "qty": 1})
    with pytest.raises(FranchiseOrderChangeError) as caught:
        parse_franchise_order_event(raw)
    assert caught.value.code == "duplicate_product"


def test_event_is_immutable():
    parsed = parse_franchise_order_event(payload())
    with pytest.raises(FrozenInstanceError):
        parsed.emp_code = "E002"
    with pytest.raises(FrozenInstanceError):
        parsed.details[0].qty = 99
    with pytest.raises(TypeError):
        parsed.details[0] = BranchOrderItemEvent(prod_code="A002", qty=1)
