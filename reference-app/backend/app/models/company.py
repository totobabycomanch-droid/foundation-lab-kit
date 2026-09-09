from typing import Optional

from pydantic import BaseModel


class CompanyCreate(BaseModel):
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
    id: Optional[str] = None
    dept_code: str
    dept_name: str
    is_used: str = "Y"
    manager_id: Optional[str] = None


class Employee(BaseModel):
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

