"""Prepared role and state checks for the separate company-boundary exercise."""
from fastapi import HTTPException


def check_permission(user, order):
    if user.role != "MANAGER":
        raise HTTPException(403, "승인 권한이 없습니다.")
    if order["status"] != "PENDING":
        raise HTTPException(409, "승인 대기 발주만 승인할 수 있습니다.")
