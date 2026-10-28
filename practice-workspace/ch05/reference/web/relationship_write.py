"""선택 비교용 상품 처리. 기본 생성·검증에서 읽지 않는다."""
from .contracts import MovementError


def change_product(db, product_code, action):
    if db.execute('SELECT id FROM lab_product WHERE code = ?', (product_code,)).fetchone() is None:
        raise MovementError(404, '상품을 찾을 수 없습니다.')
    if action == 'delete':
        db.execute('DELETE FROM lab_product WHERE code = ?', (product_code,))
    elif action == 'discontinue':
        db.execute('UPDATE lab_product SET is_deleted = 1 WHERE code = ?', (product_code,))
    else:
        raise MovementError(422, '상품 처리 구분을 확인하세요.')
