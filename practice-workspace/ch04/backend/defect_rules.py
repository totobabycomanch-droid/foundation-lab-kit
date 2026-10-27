"""Prepared role and state checks for the separate company-boundary exercise."""
from fastapi import HTTPException


def check_permission(user, order):
    """결함 공간에서 관리자 역할과 승인 대기 상태를 검사한다.

    역할이 맞지 않으면 403, 상태가 맞지 않으면 409 예외로 저장을 막는다.
    통과하면 값을 반환하지 않고 호출한 쪽의 다음 처리로 이어진다.
    회사 범위의 조회는 이 함수가 아닌 defect_scope에서 담당한다.
    """
    if user.role != "MANAGER":
        raise HTTPException(403, "승인 권한이 없습니다.")
    if order["status"] != "PENDING":
        raise HTTPException(409, "승인 대기 발주만 승인할 수 있습니다.")
