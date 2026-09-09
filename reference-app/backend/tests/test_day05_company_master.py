"""Day 5 파트너 등록의 인증 경계와 온보딩 계약 테스트."""

from copy import deepcopy

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.models.company import CompanyCreate
from app.routers import company


class MemoryResponse:
    def __init__(self, data=None):
        self.data = data or []


class MemoryQuery:
    def __init__(self, db, table_name):
        self.db = db
        self.table_name = table_name
        self.operation = "select"
        self.values = None
        self.filters = []

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, field, value):
        self.filters.append(("eq", field, value))
        return self

    def like(self, field, value):
        self.filters.append(("like", field, value))
        return self

    def insert(self, values):
        self.operation = "insert"
        self.values = deepcopy(values)
        return self

    def execute(self):
        if self.operation == "insert":
            saved = deepcopy(self.values)
            saved.setdefault("id", f"{self.table_name}-uuid")
            self.db.tables.setdefault(self.table_name, []).append(saved)
            return MemoryResponse([deepcopy(saved)])

        rows = deepcopy(self.db.tables.get(self.table_name, []))
        for operation, field, value in self.filters:
            if operation == "eq":
                rows = [row for row in rows if row.get(field) == value]
            elif operation == "like":
                prefix = value.rstrip("%")
                rows = [row for row in rows if str(row.get(field, "")).startswith(prefix)]
        return MemoryResponse(rows)


class MemoryDb:
    def __init__(self):
        self.tables = {"companies": [], "corp_class": [{"class_name": "사장", "class_code": 1}]}

    def table(self, table_name):
        return MemoryQuery(self, table_name)


class DbMustNotBeUsed:
    def table(self, _table_name):
        raise AssertionError("권한 거부 뒤에는 DB를 호출하면 안 됩니다.")


def request_with_bearer(token="day05-token"):
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/companies",
            "headers": [(b"authorization", f"Bearer {token}".encode())],
            "client": ("127.0.0.1", 50000),
        }
    )


def franchise_payload(**overrides):
    values = {
        "corp_code": "AUTO",
        "corp_id": "branch01",
        "password": "branch-password",
        "name_kr": "가맹점01",
        "tel_no": "02-3456-3456",
        "corp_category": "20",
    }
    values.update(overrides)
    return CompanyCreate(**values)


@pytest.fixture(autouse=True)
def ignore_audit_storage(monkeypatch):
    monkeypatch.setattr(company, "insert_audit_log", lambda **_kwargs: None)


@pytest.mark.asyncio
async def test_public_registration_allows_only_new_franchise():
    db = MemoryDb()

    result = await company.register_franchise(
        franchise_payload(corp_code="CLIENT-VALUE"),
        request_with_bearer(),
        db,
    )

    assert result["status"] == "success"
    assert db.tables["companies"][0]["corp_code"] == "F001"
    assert company.verify_password(
        "branch-password", db.tables["companies"][0]["password"]
    )
    assert company.verify_password(
        "branch-password", db.tables["employees"][0]["password"]
    )
    assert db.tables["employees"][0]["password"] != "branch-password"


@pytest.mark.asyncio
async def test_public_registration_rejects_supplier():
    with pytest.raises(HTTPException) as exc_info:
        await company.register_franchise(
            franchise_payload(corp_category="30"),
            request_with_bearer(),
            DbMustNotBeUsed(),
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "공개 가입은 가맹점만 가능합니다."


@pytest.mark.asyncio
async def test_new_company_requires_password_on_server():
    with pytest.raises(HTTPException) as exc_info:
        await company.register_franchise(
            franchise_payload(password=None),
            request_with_bearer(),
            DbMustNotBeUsed(),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "신규 등록 시 비밀번호는 필수입니다."


@pytest.mark.asyncio
async def test_partner_management_accepts_hq_company_bearer_token(monkeypatch):
    received = {}
    audit_records = []

    async def verify_token(token=None):
        received["token"] = token
        return {
            "user_id": "hq-company-uuid",
            "corp_id": "admin",
            "corp_category": "10",
            "role": "STAFF",
            "user_type": "company",
        }

    monkeypatch.setattr(company, "verify_token", verify_token)
    monkeypatch.setattr(
        company,
        "insert_audit_log",
        lambda **values: audit_records.append(values),
    )
    db = MemoryDb()

    result = await company.register_company(
        franchise_payload(), request_with_bearer("hq-token"), db=db
    )

    assert result["status"] == "success"
    assert received["token"] == "hq-token"
    assert audit_records[0]["user_id"] == "hq-company-uuid"


@pytest.mark.asyncio
async def test_partner_management_rejects_non_hq_user(monkeypatch):
    async def verify_token(_token=None):
        return {
            "user_id": "branch-manager",
            "corp_id": "branch01",
            "corp_category": "20",
            "role": "MANAGER",
            "user_type": "employee",
        }

    monkeypatch.setattr(company, "verify_token", verify_token)

    with pytest.raises(HTTPException) as exc_info:
        await company.register_company(
            franchise_payload(), request_with_bearer(), db=DbMustNotBeUsed()
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "파트너 정보는 본사 관리자만 변경할 수 있습니다."
