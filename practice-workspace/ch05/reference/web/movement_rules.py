"""선택 비교용 구현. 생성·검증 프롬프트에서 답안으로 읽지 않는다."""
from .contracts import MovementError


def decide_movement(direction, quantity, current_quantity):
    if direction not in ('IN', 'OUT') or type(quantity) is not int or not 1 <= quantity <= 1000000:
        raise MovementError(422, '수량은 1~1,000,000의 정수여야 합니다.')
    delta = quantity if direction == 'IN' else -quantity
    if current_quantity + delta < 0:
        raise MovementError(409, '남은 수량보다 많이 출고할 수 없습니다.')
    return delta, '입고' if direction == 'IN' else '출고'
