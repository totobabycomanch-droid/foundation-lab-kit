"""Day 5 파트너 등록의 인증 경계와 온보딩 계약 테스트."""

from copy import deepcopy

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.models.company import CompanyCreate
from app.routers import company


class MemoryResponse:
    """DB 클라이언트의 data 속성만 흉내 내는 테스트 응답이다."""
    def __init__(self, data=None):
        """테스트 객체에 필요한 초기 데이터를 보관한다."""
        self.data = data or []


class MemoryQuery:
    """선택·필터·저장 호출을 메모리 데이터에 적용하는 테스트용 쿼리다. 실제 SQL이나 DB 제약을 실행하지 않는다."""
    def __init__(self, db, table_name):
        """테스트 객체에 필요한 초기 데이터를 보관한다."""
        self.db = db
        self.table_name = table_name
        self.operation = "select"
        self.values = None
        self.filters = []

    def select(self, *_args, **_kwargs):
        """조회 호출 형식을 받아 현재 쿼리를 반환한다. 컬럼별 투영은 구현하지 않는다."""
        return self

    def eq(self, field, value):
        """필드와 같은 값만 남길 조회 조건을 기록하고 현재 쿼리를 반환한다."""
        self.filters.append(("eq", field, value))
        return self

    def like(self, field, value):
        """접두어로 비교할 조회 조건을 기록하고 현재 쿼리를 반환한다."""
        self.filters.append(("like", field, value))
        return self

    def insert(self, values):
        """저장할 값을 복사해 보관하고 현재 쿼리를 반환한다. 아직 행을 추가하지 않는다."""
        self.operation = "insert"
        self.values = deepcopy(values)
        return self

    def execute(self):
        """보관한 저장 요청 또는 조회 조건을 메모리에 적용하고 MemoryResponse를 반환한다."""
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
    """테이블별 행을 메모리에 보관하는 DB 대체 구현이다. 실제 DB 연결·트랜잭션·고유 제약 검증은 하지 않는다."""
    def __init__(self):
        """테스트 객체에 필요한 초기 데이터를 보관한다."""
        self.tables = {"companies": [], "corp_class": [{"class_name": "사장", "class_code": 1}]}

    def table(self, table_name):
        """테이블 이름을 받아 해당 테이블용 MemoryQuery를 반환한다."""
        return MemoryQuery(self, table_name)


class DbMustNotBeUsed:
    """테스트 경로에서 저장소 접근이 발생하면 즉시 실패시키는 감시용 대체 객체다."""
    def table(self, _table_name):
        """이 객체로 DB에 접근하면 테스트 실패를 발생시킨다."""
        raise AssertionError("권한 거부 뒤에는 DB를 호출하면 안 됩니다.")


def request_with_bearer(token="day05-token"):
    """Bearer 헤더가 있는 Request 객체를 만든다. 실제 HTTP 요청은 보내지 않는다."""
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
    """가맹점 등록의 기본 입력을 만들고 overrides로 지정한 필드를 덮어쓴다."""
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
    """각 테스트에서 감사 로그 저장을 아무 작업도 하지 않는 함수로 대체한다."""
    monkeypatch.setattr(company, "insert_audit_log", lambda **_kwargs: None)


def test_public_registration_route_is_not_exposed():
    """라우터에 공개 회원가입 경로가 등록되어 있지 않은지 검사한다. 서버를 띄우거나 HTTP로 호출하지 않는다."""
    route_paths = {route.path for route in company.router.routes}

    assert "/api/v1/auth/register" not in route_paths


@pytest.mark.asyncio
async def test_new_company_requires_password_on_server(monkeypatch):
    """인증을 본사 정보로 대체하고 비밀번호 없는 신규 요청이 HTTP 400으로 거부되는지 확인한다."""
    async def verify_token(_token=None):
        """테스트가 지정한 인증 정보를 반환하도록 실제 토큰 검증을 대체한다."""
        return {
            "user_id": "hq-company-uuid",
            "corp_id": "admin",
            "corp_category": "10",
            "role": "ADMIN",
            "user_type": "company",
        }

    monkeypatch.setattr(company, "verify_token", verify_token)
    with pytest.raises(HTTPException) as exc_info:
        await company.register_company(
            franchise_payload(password=None),
            request_with_bearer(),
            DbMustNotBeUsed(),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "신규 등록 시 비밀번호는 필수입니다."


@pytest.mark.asyncio
async def test_partner_management_accepts_hq_company_bearer_token(monkeypatch):
    """본사 회사 계정의 Bearer 토큰 전달·등록 성공·감사 사용자와 비밀번호 해시 저장을 확인한다.
    인증과 DB는 대체 구현이며 실제 HTTP·DB 연동 검증은 아니다.
    """
    received = {}
    audit_records = []

    async def verify_token(token=None):
        """테스트가 지정한 인증 정보를 반환하도록 실제 토큰 검증을 대체한다."""
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
    assert company.verify_password(
        "branch-password", db.tables["companies"][0]["password"]
    )
    assert company.verify_password(
        "branch-password", db.tables["employees"][0]["password"]
    )
    assert db.tables["employees"][0]["password"] != "branch-password"


@pytest.mark.asyncio
async def test_partner_management_rejects_non_hq_user(monkeypatch):
    """가맹점 MANAGER의 등록 요청을 HTTP 403으로 거부하고 DB를 호출하지 않는지 확인한다."""
    async def verify_token(_token=None):
        """테스트가 지정한 인증 정보를 반환하도록 실제 토큰 검증을 대체한다."""
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
