"""순차 판매·재시도·키 충돌·재고 부족을 실제 SQLite 조회값으로 확인합니다."""
import sqlite3


def open_database():
    """매번 재고 5·판매 0의 독립된 메모리 DB를 만듭니다."""
    db = sqlite3.connect(":memory:")
    db.executescript("""
        CREATE TABLE stock (prod_code TEXT PRIMARY KEY, qty INTEGER NOT NULL CHECK (qty >= 0));
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY,
            request_key TEXT NOT NULL UNIQUE,
            prod_code TEXT NOT NULL,
            qty INTEGER NOT NULL CHECK (qty > 0)
        );
        INSERT INTO stock VALUES ('A001', 5);
    """)
    return db


def sell(db, request_key, prod_code, qty):
    """같은 키·내용은 기존 번호를 반환하고 충돌·재고 부족이면 변경을 확정하지 않습니다."""
    if not request_key or type(qty) is not int or qty <= 0:
        raise ValueError("입력 오류")
    with db:
        previous = db.execute(
            "SELECT id, prod_code, qty FROM sales WHERE request_key = ?", (request_key,)
        ).fetchone()
        if previous:
            if previous[1:] != (prod_code, qty):
                raise ValueError("같은 키의 내용이 다릅니다")
            return previous[0]
        changed = db.execute(
            "UPDATE stock SET qty = qty - ? WHERE prod_code = ? AND qty >= ?",
            (qty, prod_code, qty),
        )
        if changed.rowcount != 1:
            raise ValueError("재고 부족")
        saved = db.execute(
            "INSERT INTO sales(request_key, prod_code, qty) VALUES (?, ?, ?)",
            (request_key, prod_code, qty),
        )
        return saved.lastrowid


def read_state(db):
    """표시용 값을 만들지 않고 DB의 재고와 판매 행을 조회합니다."""
    return {
        "stock": db.execute("SELECT qty FROM stock WHERE prod_code = 'A001'").fetchone()[0],
        "sales": db.execute("SELECT id, request_key, prod_code, qty FROM sales ORDER BY id").fetchall(),
    }


def main():
    db = open_database()
    try:
        print("정상 판매:", sell(db, "request-1", "A001", 2), read_state(db))
        print("같은 요청 재시도:", sell(db, "request-1", "A001", 2), read_state(db))
        try:
            sell(db, "request-1", "A001", 3)
        except ValueError as error:
            print("키 충돌:", str(error), read_state(db))
    finally:
        db.close()
    db = open_database()
    try:
        try:
            sell(db, "request-2", "A001", 6)
        except ValueError as error:
            print("재고 부족:", str(error), read_state(db))
    finally:
        db.close()


if __name__ == "__main__":
    main()
