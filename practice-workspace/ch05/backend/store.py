"""Provided actual SQLite tracing, transaction boundary and independent readback."""
from pathlib import Path
import sqlite3
from threading import Lock
from .contracts import MovementError

PRODUCTS = (("A001", "샘플 상품 A"), ("B001", "샘플 상품 B"))


class Result:
    def __init__(self, rows, rowcount):
        # Learner code may edit a returned dict; the observed DB rows stay intact.
        self.rows = [dict(row) for row in rows]
        self.rowcount = rowcount

    def fetchone(self):
        return dict(self.rows[0]) if self.rows else None

    def fetchall(self):
        return [dict(row) for row in self.rows]


class TracedDB:
    def __init__(self, path, trace, phase):
        self.connection = sqlite3.connect(path, timeout=5, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.trace = trace
        self.phase = phase
        self.active = None
        self.connection.set_trace_callback(self._observed)
        self.execute("PRAGMA foreign_keys = ON")

    def _observed(self, actual_sql):
        # SQLite supplies this text from the actual execution, including bound values.
        if self.active is not None:
            self.active["executed_sql"].append(actual_sql)

    def execute(self, sql, parameters=()):
        entry = {"step": len(self.trace) + 1, "phase": self.phase,
                 "sql": sql, "parameters": list(parameters), "executed_sql": [],
                 "rows": [], "affected_rows": None, "error": None}
        self.trace.append(entry)
        self.active = entry
        try:
            cursor = self.connection.execute(sql, tuple(parameters))
            rows = [dict(r) for r in cursor.fetchall()] if cursor.description else []
            entry["rows"] = rows
            entry["affected_rows"] = cursor.rowcount if cursor.rowcount >= 0 else None
            return Result(rows, cursor.rowcount)
        except Exception as error:
            entry["error"] = type(error).__name__
            raise
        finally:
            self.active = None

    def close(self):
        self.connection.close()


class LabStore:
    def __init__(self, path: Path):
        self.path = path
        self.gate = Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS products (code TEXT PRIMARY KEY, name TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS stock (
                    product_code TEXT PRIMARY KEY REFERENCES products(code),
                    quantity INTEGER NOT NULL CHECK(quantity >= 0));
                CREATE TABLE IF NOT EXISTS stock_history (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_code TEXT NOT NULL REFERENCES products(code),
                    change_qty INTEGER NOT NULL CHECK(change_qty != 0),
                    reason TEXT NOT NULL CHECK(reason IN ('입고','출고')));
            """)
            db.executemany("INSERT OR IGNORE INTO products VALUES (?, ?)", PRODUCTS)
            db.executemany("INSERT OR IGNORE INTO stock VALUES (?, 0)", [(p[0],) for p in PRODUCTS])

    def _snapshot(self, code, trace):
        # Read a consistent snapshot through a NEW connection after commit/rollback.
        db = TracedDB(self.path, trace, "저장 후 재조회")
        try:
            db.execute("BEGIN")
            products = db.execute("SELECT code, name FROM products ORDER BY code").fetchall()
            current = db.execute("SELECT product_code, quantity FROM stock WHERE product_code = ?", (code,)).fetchone()
            history = db.execute("SELECT seq, product_code, change_qty, reason FROM stock_history WHERE product_code = ? ORDER BY seq", (code,)).fetchall()
            total = db.execute("SELECT COALESCE(SUM(change_qty), 0) AS quantity FROM stock_history WHERE product_code = ?", (code,)).fetchone()
            db.execute("COMMIT")
            return {"products": products, "current": current, "history": history, "history_quantity": total["quantity"]}
        finally:
            db.close()

    def observe(self, code, trace):
        with self.gate:
            return self._snapshot(code, trace)

    def move(self, code, direction, quantity, apply, decide, trace):
        with self.gate:
            db = TracedDB(self.path, trace, "입출고 처리")
            status, detail, outcome = 200, "입출고를 저장했습니다.", "확정"
            try:
                db.execute("BEGIN IMMEDIATE")
                apply(db, code, direction, quantity, decide)
                db.execute("COMMIT")
            except Exception as error:
                if db.connection.in_transaction:
                    db.execute("ROLLBACK")
                outcome = "취소"
                if isinstance(error, MovementError):
                    status, detail = error.status, error.detail
                else:
                    status, detail = 500, "저장하지 못했습니다. 실행 상세와 AI 검증으로 원인을 확인하세요."
            finally:
                db.close()
            return status, detail, outcome, self._snapshot(code, trace)

    def reset(self, code, trace):
        with self.gate:
            db = TracedDB(self.path, trace, "실습 1 초기화")
            try:
                db.execute("BEGIN IMMEDIATE")
                db.execute("DELETE FROM stock_history")
                db.execute("UPDATE stock SET quantity = 0")
                db.execute("COMMIT")
            except Exception:
                if db.connection.in_transaction:
                    db.execute("ROLLBACK")
                raise
            finally:
                db.close()
            return self._snapshot(code, trace)
