"""Chapter 2에서 조사하는 가맹점 입고확정 HTTP 계약 테스트."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient

from app.core import idempotency as idempotency_core
from app.routers import purchase


BRANCH_AUTH = {
    "user_id": "11111111-1111-4111-8111-111111111118",
    "corp_id": "branch01",
    "corp_category": "20",
}


class Response:
    def __init__(self, data=None):
        self.data = data


async def verify_branch_token(token=None):
    if not token:
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")
    return dict(BRANCH_AUTH)


class IdempotencyQuery:
    def __init__(self, db, operation="select", values=None):
        self.db = db
        self.operation = operation
        self.values = values or {}
        self.filters = []

    def select(self, *_args):
        self.operation = "select"
        return self

    def insert(self, values):
        self.operation = "insert"
        self.values = deepcopy(values)
        return self

    def update(self, values):
        self.operation = "update"
        self.values = deepcopy(values)
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def limit(self, _value):
        return self

    def execute(self):
        def matches(row):
            return all(row.get(field) == value for field, value in self.filters)

        if self.operation == "select":
            return Response([deepcopy(row) for row in self.db.rows if matches(row)])
        if self.operation == "insert":
            record = deepcopy(self.values)
            record.setdefault(
                "expires_at",
                (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            )
            self.db.rows.append(record)
            return Response([deepcopy(record)])
        updated = []
        for row in self.db.rows:
            if matches(row):
                row.update(self.values)
                updated.append(deepcopy(row))
        return Response(updated)


class IdempotencyDb:
    def __init__(self):
        self.rows = []

    def table(self, name):
        assert name == "idempotency_keys"
        return IdempotencyQuery(self)


class PurchaseOrderQuery:
    def __init__(self, rows):
        self.rows = rows
        self.filters = []

    def select(self, *_args):
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def execute(self):
        return Response(
            [
                deepcopy(row)
                for row in self.rows
                if all(row.get(field) == value for field, value in self.filters)
            ]
        )


class TenantDb:
    def __init__(self, rows):
        self.rows = rows
        self.table_calls = []

    def table(self, name):
        self.table_calls.append(name)
        assert name == "purchaseorder10"
        return PurchaseOrderQuery(self.rows)

    def rpc(self, *_args, **_kwargs):
        raise AssertionError("RPC는 tenant DB가 아니라 system DB로 호출해야 합니다.")


class SystemDb:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.rpc_calls = []

    def rpc(self, name, params):
        self.rpc_calls.append((name, params))
        return self

    def execute(self):
        if self.error:
            raise self.error
        return Response(self.result)


class RpcError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def success_payload():
    return {
        "status": "success",
        "data": {
            "purchase_order_no": 209908160101,
            "stock_inbound_no": 1,
            "order_status": "60",
        },
    }


@pytest.fixture
def context(monkeypatch):
    app = FastAPI()
    app.include_router(purchase.router)
    tenant_db = TenantDb(
        [{"purchase_order_no": 209908160101, "corp_id": "branch01", "order_status": "60"}]
    )
    idempotency_db = IdempotencyDb()
    system_db = SystemDb(success_payload())

    async def tenant_dependency():
        return tenant_db

    monkeypatch.setattr(purchase, "verify_token", verify_branch_token)
    monkeypatch.setattr(purchase, "get_system_db", lambda: system_db)
    monkeypatch.setattr(idempotency_core, "verify_token", verify_branch_token)
    monkeypatch.setattr(idempotency_core, "get_system_db", lambda: idempotency_db)
    app.dependency_overrides[purchase.get_tenant_db] = tenant_dependency
    return app, tenant_db, idempotency_db, system_db


async def post_status(app, *, key=None, payload=None, token="branch-token"):
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Idempotency-Key"] = key
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(
            f"/api/v1/purchase_orders/status_store?token={token}",
            headers=headers,
            json=payload or {"purchase_order_no": 209908160101, "status": "60"},
        )


@pytest.mark.asyncio
async def test_status_store_requires_idempotency_header(context):
    app, _tenant, _keys, system = context
    response = await post_status(app)
    assert response.status_code == 422
    assert system.rpc_calls == []


@pytest.mark.asyncio
async def test_status_store_rejects_status_other_than_60(context):
    app, _tenant, _keys, system = context
    response = await post_status(
        app,
        key=str(uuid4()),
        payload={"purchase_order_no": 209908160101, "status": "40"},
    )
    assert response.status_code == 403
    assert system.rpc_calls == []


@pytest.mark.asyncio
async def test_status_store_uses_authenticated_company_for_rpc(context):
    app, tenant, keys, system = context
    response = await post_status(app, key=str(uuid4()))
    assert response.status_code == 200, response.text
    name, params = system.rpc_calls[0]
    assert name == "fn_process_purchase_receipt"
    assert params == {
        "p_po_no": 209908160101,
        "p_corp_id": "branch01",
        "p_user_id": BRANCH_AUTH["user_id"],
    }
    assert tenant.table_calls == ["purchaseorder10"]
    assert keys.rows[0]["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_status_store_ignores_corp_id_in_payload(context):
    app, _tenant, _keys, system = context
    response = await post_status(
        app,
        key=str(uuid4()),
        payload={
            "purchase_order_no": 209908160101,
            "status": "60",
            "corp_id": "tampered-corp",
        },
    )
    assert response.status_code == 200
    assert system.rpc_calls[0][1]["p_corp_id"] == "branch01"


@pytest.mark.asyncio
async def test_status_store_replays_same_key_without_second_rpc(context):
    app, _tenant, _keys, system = context
    key = str(uuid4())
    first = await post_status(app, key=key)
    second = await post_status(app, key=key)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()
    assert second.headers["Idempotency-Replayed"] == "true"
    assert len(system.rpc_calls) == 1


@pytest.mark.asyncio
async def test_status_store_maps_business_error_to_conflict(context):
    app, _tenant, _keys, system = context
    system.error = RpcError("P0001", "발주서 상태가 변경되어 입고를 확정할 수 없습니다.")
    response = await post_status(app, key=str(uuid4()))
    assert response.status_code == 409
    assert response.json()["detail"] == "발주서 상태가 변경되어 입고를 확정할 수 없습니다."
