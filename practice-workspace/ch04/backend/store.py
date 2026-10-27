"""Fixed SQLite data and reset boundary; one database per workspace."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from threading import Lock

SEEDS = (
    (1001, "A", "A회사 승인 대기 발주", 2, "PENDING", 0),
    (1002, "A", "A회사 승인 완료 발주", 3, "APPROVED", 1),
    (2001, "B", "B회사 승인 대기 발주", 4, "PENDING", 0),
)


class LabStore:
    def __init__(self, path: Path):
        self.path = path
        self._activity = Lock()
        self._active = 0
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY, corp_id TEXT NOT NULL,
                item_name TEXT NOT NULL, quantity INTEGER NOT NULL,
                status TEXT NOT NULL, approval_count INTEGER NOT NULL
            )""")
            # Initialization never overwrites changes made in an earlier server run.
            db.executemany("INSERT OR IGNORE INTO orders VALUES (?, ?, ?, ?, ?, ?)", SEEDS)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @contextmanager
    def operation(self):
        with self._activity:
            self._active += 1
        try:
            yield
        finally:
            with self._activity:
                self._active -= 1

    def reset(self, clear_sessions) -> bool:
        with self._activity:
            if self._active:
                return False
            with self.connect() as db:
                db.execute("DELETE FROM orders")
                db.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", SEEDS)
            clear_sessions()
            return True

    def list_orders(self, corp_id: str) -> list[dict]:
        with self.connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM orders WHERE corp_id = ? ORDER BY id", (corp_id,)
            )]

    def find_order(self, order_id: int, corp_id: str) -> dict | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM orders WHERE id = ? AND corp_id = ?", (order_id, corp_id)
            ).fetchone()
            return dict(row) if row else None

    def approve_order(self, order_id: int, user, check_permission) -> dict | None:
        """Keep scope, current-state inspection and writes in one transaction."""
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM orders WHERE id = ? AND corp_id = ?", (order_id, user.corp_id)
            ).fetchone()
            if row is None:
                return None
            order = dict(row)
            # A rule failure raises before either write; the connection rolls back.
            check_permission(user, order)
            changed = db.execute(
                """UPDATE orders SET status = 'APPROVED', approval_count = approval_count + 1
                   WHERE id = ? AND corp_id = ? AND status = ? AND approval_count = ?""",
                (order_id, user.corp_id, order["status"], order["approval_count"]),
            )
            if changed.rowcount != 1:
                raise RuntimeError("Order changed before approval")
            return dict(db.execute("SELECT * FROM orders WHERE id = ? AND corp_id = ?",
                                   (order_id, user.corp_id)).fetchone())
