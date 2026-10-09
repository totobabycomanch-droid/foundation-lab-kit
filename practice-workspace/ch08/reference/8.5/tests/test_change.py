# 파일 경로: project/tests/test_change.py
# 요청 검증만 DB 없이 검사합니다
from dataclasses import FrozenInstanceError

import pytest

from services.franchise_order import (
    BranchOrderEvent,
    BranchOrderItemEvent,
    FranchiseOrderChangeError,
    parse_franchise_order_event,
    ProductSnapshot,
    decide_franchise_order,
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


def event(is_vat="2"):
    return BranchOrderEvent(
        dept_code="10",
        emp_code="E001",
        delivery_code=101,
        is_vat=is_vat,
        details=(BranchOrderItemEvent(prod_code="A001", qty=5),),
    )


def products(unit_price=1000, is_active=True):
    return {
        "A001": ProductSnapshot(
            prod_code="A001", unit_price=unit_price, is_active=is_active
        )
    }


def test_decide_uses_server_price_and_calculates_vat():
    plan = decide_franchise_order(event(), products=products())

    assert (plan.corp_id, plan.partner_id, plan.order_status) == (
        "branch01",
        "admin",
        "10",
    )
    assert (plan.details[0].net_price, plan.details[0].vat) == (5000, 500)
    assert plan.total_amount == 5500


def test_decide_calculates_zero_vat_when_is_vat_is_one():
    plan = decide_franchise_order(event(is_vat="1"), products=products())
    assert (plan.details[0].vat, plan.total_amount) == (0, 5000)


@pytest.mark.parametrize(
    "available, code",
    [
        ({}, "product_not_found"),
        (products(is_active=False), "product_not_found"),
        (products(unit_price=0), "invalid_unit_price"),
    ],
)
def test_decide_rejects_unusable_server_product(available, code):
    with pytest.raises(FranchiseOrderChangeError) as caught:
        decide_franchise_order(event(), products=available)
    assert caught.value.code == code



def test_vat_rounds_half_up():
    plan = decide_franchise_order(event(), products=products(unit_price=201))
    assert (plan.details[0].net_price, plan.details[0].vat, plan.total_amount) == (1005, 101, 1106)


def test_server_actor_and_plan_are_immutable():
    plan = decide_franchise_order(event(), products=products(), actor_corp_id="branch02")
    assert plan.corp_id == "branch02"
    assert isinstance(plan.details, tuple)
    with pytest.raises(FrozenInstanceError):
        plan.total_amount = 1
    with pytest.raises(FrozenInstanceError):
        plan.details[0].unit_price = 1


def test_negative_server_price_is_rejected():
    with pytest.raises(FranchiseOrderChangeError) as caught:
        decide_franchise_order(event(), products=products(unit_price=-1000))
    assert caught.value.code == "invalid_unit_price"
