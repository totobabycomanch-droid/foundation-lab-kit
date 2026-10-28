"""독립된 메모리 DB에서 중간 확정과 전체 롤백의 차이를 확인합니다."""
import sqlite3


def observe_failure(commit_stock_first):
    """재고 10·주문 0에서 차감 후 주문 INSERT가 실패하면 실제 DB 상태를 반환합니다."""
    db = sqlite3.connect(":memory:")
    try:
        db.executescript("""
            CREATE TABLE stock (qty INTEGER NOT NULL CHECK (qty >= 0));
            CREATE TABLE orders (id INTEGER PRIMARY KEY, qty INTEGER NOT NULL CHECK (qty > 0));
            INSERT INTO stock VALUES (10);
        """)
        failed = False
        try:
            with db:
                db.execute("UPDATE stock SET qty = qty - 1")
                if commit_stock_first:
                    db.commit()  # 차감만 확정하면 뒤의 실패로 이 변경을 취소할 수 없습니다.
                db.execute("INSERT INTO orders(qty) VALUES (0)")  # 의도적인 저장 실패
        except sqlite3.IntegrityError:
            failed = True
        return {
            "failed": failed,
            "stock": db.execute("SELECT qty FROM stock").fetchone()[0],
            "orders": db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        }
    finally:
        db.close()


if __name__ == "__main__":
    print("중간 확정 후 실패:", observe_failure(True))
    print("같은 트랜잭션에서 실패:", observe_failure(False))
