import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.audit import insert_audit_log
from app.core.database import get_tenant_db
from app.core.security import get_password_hash, verify_password, verify_token
from app.models.company import CompanyCreate


logger = logging.getLogger(__name__)
router = APIRouter()


def _request_token(request: Request, query_token: Optional[str]) -> Optional[str]:
    """HTTP 요청에서 인증 토큰 문자열을 꺼낸다.
    Authorization의 Bearer 값을 우선하며, 없으면 query_token을 반환한다. 토큰의 유효성은 검사하지 않는다.
    """
    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return query_token


def _require_hq_manager(auth_info: dict) -> None:
    """해석된 인증 정보가 파트너 관리 권한 조건을 충족하는지 검사한다.
    본사 회사 계정 또는 본사의 MANAGER·ADMIN 사원을 허용한다. 거부 시 HTTP 403을 발생시키며 DB는 변경하지 않는다.
    """
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
    """회사 등록 POST 요청을 인증 확인·권한 검사·저장 함수로 연결한다.
    company는 등록 대상 입력, req와 token은 요청의 인증 정보, db는 저장소다.
    검사를 통과하면 저장 함수의 결과를 반환하며, 실제 저장은 _save_company에 맡긴다.
    """
    auth_info = await verify_token(_request_token(req, token))
    _require_hq_manager(auth_info)
    return await _save_company(company, req, db, auth_info)


async def _save_company(company, req, db, auth_info):
    """신규 회사 입력을 받아 회사 저장과 가맹점의 기본 부서·관리자 생성을 순서대로 시도한다.
    비밀번호 누락·기존 업체 ID는 HTTP 400, 수정 요청은 501로 거부한다.
    회사 비밀번호를 해시로 바꾸고 DB와 감사 로그를 기록한 뒤 회사 저장 결과를 반환한다.
    각 저장 호출과 예외 처리의 범위는 아래 코드에서 확인한다.
    """
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
        try:
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
        except Exception as auto_err:
            # 이 부분 성공 결함은 Chapter 3에서 독자가 찾아낼 레거시 사례다.
            logger.error(
                "Auto-creation of staff failed for %s: %s",
                company.corp_id,
                auto_err,
            )

    return {"status": "success", "data": response.data}


@router.get("/api/v1/companies")
async def get_companies(category: str = "20", db=Depends(get_tenant_db)):
    """category와 일치하는 회사 행 목록을 DB에서 읽어 반환한다.
    기본값 20은 가맹점이며 조회 결과가 없으면 빈 목록을 반환한다.
    현재 쿼리는 모든 컬럼을 선택하며, 이 함수 자체에는 인증 정보 검사 단계가 없다.
    """
    response = db.table("companies").select("*").eq("corp_category", category).execute()
    return response.data or []


__all__ = [
    "register_company",
    "router",
    "verify_password",
]
