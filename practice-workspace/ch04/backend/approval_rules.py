"""Learner workspace: begin with the comparison behavior, not a decided policy."""


def check_permission(user, order):
    """승인 저장 전에 호출되는 업무 판단 자리다. 시작본은 아무 검사도 하지 않는다.

    user는 서버가 확인한 사용자, order는 DB에서 읽은 발주다.
    실습에서 확정한 규칙을 추가하며, 거부할 때는 예외로 저장 진행을 멈춘다.
    이 함수에서 직접 DB를 조회하거나 저장하지 않는다.
    """
    # Exercise 2: implement the confirmed approval-role policy here.
    # The initial comparison intentionally does not restrict roles or states.
    pass
