import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import Lock

from .models import OrderInput


class LabStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()
        self.requests = 0
        self.pending = 0
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, item_name TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 9999))")
            db.execute("""CREATE TABLE IF NOT EXISTS order_requests (
                request_key TEXT PRIMARY KEY,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                order_id INTEGER NOT NULL REFERENCES orders(id)
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS company_orders (
                id INTEGER PRIMARY KEY,
                corp_id TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL
            )""")
            db.executemany(
                "INSERT OR IGNORE INTO company_orders(id, corp_id, item_name, quantity) VALUES (?, ?, ?, ?)",
                [(1001, "A", "A회사 테스트 발주", 2), (2001, "B", "B회사 테스트 발주", 3)],
            )

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            with connection:
                yield connection
        finally:
            connection.close()

    def add_order(self, order: OrderInput) -> dict:
        with self.lock, self.connect() as db:
            cursor = db.execute("INSERT INTO orders(item_name, quantity) VALUES (?, ?)", (order.item_name, order.quantity))
            return {"id": cursor.lastrowid, **order.model_dump()}

    def list_orders(self) -> list[dict]:
        with self.lock, self.connect() as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute("SELECT id, item_name, quantity FROM orders ORDER BY id")]

    def begin_request(self):
        with self.lock:
            self.requests += 1
            self.pending += 1

    def end_request(self):
        with self.lock:
            self.pending -= 1

    def observations(self) -> dict:
        with self.lock:
            return {"request_count": self.requests, "pending_count": self.pending}

    def reset(self) -> bool:
        with self.lock:
            if self.pending:
                return False
            with self.connect() as db:
                db.execute("DELETE FROM order_requests")
                db.execute("DELETE FROM orders")
            self.requests = 0
            return True
