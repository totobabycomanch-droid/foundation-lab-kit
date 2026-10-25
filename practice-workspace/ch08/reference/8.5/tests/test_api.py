# 파일 경로: project/tests/test_api.py
# API 연결부의 200·400·409·500 변환과 저장 결과를 검사합니다
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import get_db
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


@pytest.fixture
def client(db):
    def override_db():
        yield db

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous


def saved_counts(db):
    with db.begin():
        return (
            db.scalar(select(func.count()).select_from(PurchaseOrder)),
            db.scalar(select(func.count()).select_from(PurchaseOrderDetail)),
            db.scalar(select(func.count()).select_from(AuditLog)),
        )


def test_route_is_registered():
    """발주 등록 POST가 앱에 등록되는지 확인합니다."""
    assert "post" in app.openapi()["paths"]["/franchise/order"]


def test_create_order_returns_fixed_success_contract(db, client):
    """단가 1000·수량 5의 발주는 200·합계 5500과 DB 1·1·1건을 남깁니다."""
    response = client.post("/franchise/order", json=payload())
    assert response.status_code == 200
    assert response.json() == {
        "status": "success", "purchase_order_no": 1, "order_status": "10",
        "detail_count": 1, "total_amount": 5500,
    }
    assert saved_counts(db) == (1, 1, 1)
    with db.begin():
        product = db.get(Product, "A001")
        assert (product.unit_price, product.is_active) == (1000, True)


@pytest.mark.parametrize("request_payload", [payload(qty=0), payload(prod_code="UNKNOWN")])
def test_create_order_maps_bad_request_to_400(db, client, request_payload):
    """수량 0과 없는 상품 요청은 400으로 거부하고 저장 기록을 남기지 않습니다."""
    response = client.post("/franchise/order", json=request_payload)
    assert response.status_code == 400
    assert saved_counts(db) == (0, 0, 0)


@pytest.mark.parametrize("request_payload", [[], "bad", 7, True, None])
def test_non_object_json_is_invalid_payload_400(db, client, request_payload):
    """배열·문자열·숫자·논리값·null JSON은 파서의 400으로 거부하며 저장하지 않습니다."""
    from services.franchise_order import FranchiseOrderChangeError, parse_franchise_order_event

    with pytest.raises(FranchiseOrderChangeError) as caught:
        parse_franchise_order_event(request_payload)
    assert caught.value.code == "invalid_payload"
    response = client.post(
        "/franchise/order", content=json.dumps(request_payload),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == str(caught.value)
    assert saved_counts(db) == (0, 0, 0)


def test_create_order_maps_invalid_server_price_to_409(db, client):
    """서버 상품 단가가 0이면 409를 반환하고 발주를 저장하지 않습니다."""
    with db.begin():
        db.get(Product, "A001").unit_price = 0
    response = client.post("/franchise/order", json=payload())
    assert response.status_code == 409
    assert saved_counts(db) == (0, 0, 0)


def test_create_order_maps_integrity_error_to_409(db, client, monkeypatch):
    """저장 함수의 무결성 예외는 내부 SQL을 노출하지 않는 409로 변환합니다."""
    def fail_storage(_plan, _db):
        raise IntegrityError("private SQL", {}, RuntimeError("private constraint"))

    monkeypatch.setattr(order_router, "persist_franchise_order", fail_storage)
    response = client.post("/franchise/order", json=payload())
    assert response.status_code == 409
    assert "private" not in response.text
    assert saved_counts(db) == (0, 0, 0)


def test_create_order_hides_unexpected_storage_error(db, client, monkeypatch):
    """저장 함수의 일반 예외는 500으로 변환하되 SQL과 예외 내용은 숨깁니다."""
    def fail_storage(_plan, _db):
        raise RuntimeError("SELECT secret internal database detail")

    monkeypatch.setattr(order_router, "persist_franchise_order", fail_storage)
    response = client.post("/franchise/order", json=payload())
    assert response.status_code == 500
    assert "SELECT" not in response.text
    assert "internal database detail" not in response.text
    assert saved_counts(db) == (0, 0, 0)
