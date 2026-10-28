"""Learner implementation: decide a movement without querying a database."""
from .contracts import MovementError


def decide_movement(direction, quantity, current_quantity):
    """입출고 구분·양의 정수 수량·현재고로 (증감 수량, 사유)를 반환한다.

    재고 부족 등 업무상 거부는 MovementError로 알린다. DB 작업은 하지 않는다.
    시작본은 아직 구현하지 않았다. 5.2의 AI 구현 요청으로 이 자리를 완성한다.
    """
    raise MovementError(501, "5.2의 AI 구현 요청으로 입출고 규칙을 먼저 완성하세요.")
