from typing import Optional

from pydantic import BaseModel


class CompanyCreate(BaseModel):
    """회사 등록 요청 본문의 필드와 자료형을 정의한다.
    corp_id는 업체 ID, corp_code는 업체 코드이며, corp_category의 기본값 20은 가맹점이다.
    이 모델은 DB에 저장하지 않으며 권한·중복·신규 비밀번호 검사는 라우터에서 확인한다.
    """
    id: Optional[str] = None
    corp_code: str
    corp_id: str
    password: Optional[str] = None
    name_kr: str
    name_en: Optional[str] = None
    biz_no: Optional[str] = None
    corp_no: Optional[str] = None
    corp_type: str = "1"
    is_sme: str = "0"
    ceo_name: Optional[str] = None
    nationality: str = "0"
    ceo_jumin: Optional[str] = None
    zip_code: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    tel_no: str
    fax: Optional[str] = None
    biz_type_code: Optional[str] = None
    biz_status: Optional[str] = None
    branch_type: str = "0"
    main_office_code: Optional[str] = None
    fiscal_year: Optional[int] = None
    corp_category: str = "20"
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_holder: Optional[str] = None
    responsible_emp_id: Optional[str] = None


class Department(BaseModel):
    """부서 입력의 필드와 자료형을 정의한다. dept_code는 부서 코드, dept_name은 부서명이다.
    이 모델 자체는 부서 저장이나 회사 소유권 검사를 수행하지 않는다.
    """
    id: Optional[str] = None
    dept_code: str
    dept_name: str
    is_used: str = "Y"
    manager_id: Optional[str] = None


class Employee(BaseModel):
    """사원 입력의 필드와 자료형을 정의한다. dept_id는 소속 부서, user_id는 로그인 ID다.
    role의 기본값은 STAFF이며, 실제 권한 검사와 저장은 이 모델 밖에서 수행한다.
    """
    id: Optional[str] = None
    dept_id: str
    emp_code: Optional[str] = None
    emp_name: str
    class_code: Optional[int] = None
    join_date: Optional[str] = None
    tel_no: Optional[str] = None
    is_working: str = "Y"
    user_id: Optional[str] = None
    password: Optional[str] = None
    role: str = "STAFF"

