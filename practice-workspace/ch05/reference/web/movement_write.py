"""선택 비교용 구현. 제공된 DB만 사용하고 transaction은 기반에 맡긴다."""
from .contracts import MovementError


def apply_movement(db, product_code, direction, quantity, decide_movement):
    row = db.execute('SELECT quantity FROM stock WHERE product_code = ?', (product_code,)).fetchone()
    if row is None:
        raise MovementError(404, '품목을 찾을 수 없습니다.')
    delta, reason = decide_movement(direction, quantity, row['quantity'])
    db.execute('UPDATE stock SET quantity = quantity + ? WHERE product_code = ?', (delta, product_code))
    db.execute('INSERT INTO stock_history (product_code, change_qty, reason) VALUES (?, ?, ?)',
               (product_code, delta, reason))
