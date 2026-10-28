"""선택 비교용 구현. 기본 AI 생성·검증에서는 읽지 않는다."""
import sqlite3


def run_transaction(db, quantity, commit_early):
    """주문 저장 실패 때 이번 거래를 취소하고 실제 DB 예외를 전달한다."""
    try:
        db.execute('BEGIN')
        db.execute('UPDATE stock SET qty=qty-? WHERE prod_code=?', (quantity,'A001'))
        if commit_early:
            db.commit()
        db.execute('INSERT INTO orders(qty) VALUES (?)', (0,))
        db.commit()
    except Exception:
        db.rollback()
        raise
