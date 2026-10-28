"""Learner implementation: read, decide, update stock and append history."""
from .contracts import MovementError


def apply_movement(db, product_code, direction, quantity, decide_movement):
    """제공된 추적 DB로 현재고를 읽고 판단 후 현재고와 이력을 저장한다.

    db.execute(sql, parameters)의 결과는 fetchone/fetchall/rowcount를 지원한다.
    트랜잭션과 저장 후 재조회는 제공 기반이 담당한다. 이 함수는 연결·확정·취소를
    직접 만들지 않는다. 회사·사용자·다른 실습 데이터는 다루지 않는다.
    """
    raise MovementError(501, "5.2의 AI 구현 요청으로 입출고 저장을 먼저 완성하세요.")
