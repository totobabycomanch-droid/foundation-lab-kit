"""학습자가 완성할 상품 삭제·취급 중단 처리."""
from .contracts import MovementError


def change_product(db, product_code, action):
    """action은 delete/discontinue. 제공 추적 DB로 대상 확인 후 처리한다.

    없는 상품은 404로 거부한다. delete는 실제 DELETE를 시도하고 DB 외래 키
    오류를 숨기지 않는다. discontinue는 상품 행을 남기고 is_deleted=1로 바꾼다.
    연결·확정·취소는 제공 기반이 담당한다. 실습 1 테이블은 다루지 않는다.
    """
    raise MovementError(501, "5.4의 AI 구현 요청으로 상품 처리를 먼저 완성하세요.")
