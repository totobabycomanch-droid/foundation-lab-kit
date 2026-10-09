# 파일 경로: project/tests/test_api.py
# API 연결부의 200·400·409·500 변환과 저장 결과를 검사합니다
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from models import AuditLog, Base, Product, PurchaseOrder, PurchaseOrderDetail
from routers import franchise_order as order_router


def payload(prod_code="A001", qty=5):
    return {
        "master": {
            "dept_code": "10",
            "emp_code": "E001",
            "delivery_code": 101,
            "is_vat": "2",
        },
        "details": [{"prod_code": prod_code, "qty": qty}],
    }


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autocommit=False, autoflush=False)()
    with session.begin():
        session.add(Product(prod_code="A001", unit_price=1000, is_active=True))
    yield session
    session.close()
    engine.dispose()


def saved_counts(db):
    with db.begin():
        return (
            db.scalar(select(func.count()).select_from(PurchaseOrder)),
            db.scalar(select(func.count()).select_from(PurchaseOrderDetail)),
            db.scalar(select(func.count()).select_from(AuditLog)),
        )


def test_route_is_registered():
    assert "post" in app.openapi()["paths"]["/franchise/order"]


def test_create_order_returns_fixed_success_contract(db):
    result = order_router.create_franchise_order(payload(), db)

    assert result == {
        "status": "success",
        "purchase_order_no": 1,
        "order_status": "10",
        "detail_count": 1,
        "total_amount": 5500,
    }
    assert saved_counts(db) == (1, 1, 1)


@pytest.mark.parametrize(
    "request_payload, expected_status",
    [
        (payload(qty=0), 400),
        (payload(prod_code="UNKNOWN"), 400),
    ],
)
def test_create_order_maps_bad_request_to_400(db, request_payload, expected_status):
    with pytest.raises(HTTPException) as caught:
        order_router.create_franchise_order(request_payload, db)
    assert caught.value.status_code == expected_status
    assert saved_counts(db) == (0, 0, 0)


def test_create_order_maps_invalid_server_price_to_409(db):
    with db.begin():
        db.get(Product, "A001").unit_price = 0

    with pytest.raises(HTTPException) as caught:
        order_router.create_franchise_order(payload(), db)
    assert caught.value.status_code == 409
    assert saved_counts(db) == (0, 0, 0)


def test_create_order_hides_unexpected_storage_error(db, monkeypatch):
    def fail_storage(_plan, _db):
        raise RuntimeError("internal database detail")

    monkeypatch.setattr(order_router, "persist_franchise_order", fail_storage)
    with pytest.raises(HTTPException) as caught:
        order_router.create_franchise_order(payload(), db)

    assert caught.value.status_code == 500
    assert "internal database detail" not in caught.value.detail
    assert saved_counts(db) == (0, 0, 0)
