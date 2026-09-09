from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.audit import insert_audit_log
from app.core.database import get_tenant_db
from app.core.security import get_password_hash, verify_password, verify_token
from app.models.company import CompanyCreate


router = APIRouter()


def _request_token(request: Request, query_token: Optional[str]) -> Optional[str]:
    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return query_token


def _require_hq_manager(auth_info: dict) -> None:
    is_hq = str(auth_info.get("corp_category") or "") == "10"
    is_company_account = auth_info.get("user_type") == "company"
    is_manager = auth_info.get("role") in ("MANAGER", "ADMIN")
    if not is_hq or not (is_company_account or is_manager):
        raise HTTPException(
            status_code=403,
            detail="파트너 정보는 본사 관리자만 변경할 수 있습니다.",
        )


@router.post("/api/v1/companies")
async def register_company(
    company: CompanyCreate,
    req: Request,
    token: Optional[str] = None,
    db=Depends(get_tenant_db),
):
    auth_info = await verify_token(_request_token(req, token))
    _require_hq_manager(auth_info)
    return await _save_company(company, req, db, auth_info)


@router.post("/api/v1/auth/register")
async def register_franchise(
    company: CompanyCreate,
    req: Request,
    db=Depends(get_tenant_db),
):
    if company.id is not None:
        raise HTTPException(status_code=400, detail="공개 가입에서는 신규 등록만 가능합니다.")
    if company.corp_category != "20":
        raise HTTPException(status_code=403, detail="공개 가입은 가맹점만 가능합니다.")
    company.corp_code = "AUTO"
    return await _save_company(company, req, db, auth_info=None)


async def _save_company(company, req, db, auth_info):
    if not company.id and not company.password:
        raise HTTPException(status_code=400, detail="신규 등록 시 비밀번호는 필수입니다.")
    if company.id:
        raise HTTPException(status_code=501, detail="참조 앱에서는 신규 등록만 검증합니다.")

    existing = (
        db.table("companies")
        .select("corp_id")
        .eq("corp_id", company.corp_id)
        .execute()
    )
    if existing.data:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

    prefix = {"10": "H", "20": "F", "30": "S"}.get(company.corp_category, "C")
    codes = db.table("companies").select("corp_code").like("corp_code", f"{prefix}%").execute()
    numbers = []
    for row in codes.data or []:
        suffix = str(row.get("corp_code", ""))[1:]
        if suffix.isdigit():
            numbers.append(int(suffix))
    company.corp_code = f"{prefix}{(max(numbers) + 1 if numbers else 1):03d}"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    data = company.model_dump(exclude={"id"})
    data["password"] = get_password_hash(company.password)
    data.update({"create_date": now, "update_date": now})
    response = db.table("companies").insert(data).execute()

    insert_audit_log(
        db=db,
        corp_id=company.corp_id,
        table_name="companies",
        record_id=response.data[0].get("id", "Unknown"),
        action="INSERT",
        user_id=auth_info.get("user_id", "System") if auth_info else "System",
    )

    # 의도적으로 별도 INSERT를 순서대로 실행한다. 이 참조 흐름에는 아직
    # 세 저장을 하나로 묶는 트랜잭션 경계가 없다.
    if company.corp_category == "20":
        department = db.table("departments").insert(
            {"corp_id": company.corp_id, "dept_code": "99", "dept_name": "관리자"}
        ).execute()
        classes = (
            db.table("corp_class")
            .select("class_code")
            .eq("class_name", "사장")
            .execute()
        )
        db.table("employees").insert(
            {
                "corp_id": company.corp_id,
                "dept_id": department.data[0]["id"],
                "emp_code": "0001",
                "emp_name": "관리자",
                "class_code": classes.data[0]["class_code"] if classes.data else 1,
                "user_id": company.corp_id,
                "password": data["password"],
                "role": "MANAGER",
            }
        ).execute()

    return {"status": "success", "data": response.data}


@router.get("/api/v1/companies")
async def get_companies(category: str = "20", db=Depends(get_tenant_db)):
    response = db.table("companies").select("*").eq("corp_category", category).execute()
    return response.data or []


__all__ = [
    "register_company",
    "register_franchise",
    "router",
    "verify_password",
]
