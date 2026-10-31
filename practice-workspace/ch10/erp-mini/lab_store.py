"""Provided PostgreSQL observation tools. Never commits learner business writes."""
from contextlib import closing
from contextvars import ContextVar
from decimal import Decimal
from uuid import UUID

from db import get_connection as raw_connection

RAMEN = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
COLA = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
COMPANY = '11111111-1111-1111-1111-111111111111'
PRICE = '11111111-2222-3333-4444-555555555555'
TABLES = ('orders', 'order_items', 'stock_ledger', 'order_events', 'order_state_history')
TRACE = ContextVar('ch10_trace', default=None)
FAIL_SECOND = ContextVar('ch10_fail_second', default=False)


def serial(value):
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return value


def sqlstate(exc):
    details = exc.args[0] if exc.args else None
    return str(details.get('C', 'unknown')) if isinstance(details, dict) else 'unknown'


def record(action, **fields):
    trace = TRACE.get()
    if trace is not None:
        trace.append(dict(step=len(trace) + 1, action=action, **fields))


def dedicated_connection():
    conn = raw_connection()
    try:
        with closing(conn.cursor()) as cur:
            cur.execute("SELECT 1 FROM foundation_lab_marker WHERE lab_id='chapter10'")
            if not cur.fetchone():
                raise RuntimeError('Chapter 10 marker missing')
        conn.rollback()  # marker lookup only; no learner writes have begun
        return conn
    except Exception:
        conn.close()
        raise


class ObservedCursor:
    def __init__(self, owner):
        self.owner = owner
        self.raw = owner.raw.cursor()

    def execute(self, sql, parameters=()):
        normalized = ' '.join(sql.lower().split())
        if normalized.startswith('insert into order_items'):
            self.owner.items += 1
            if FAIL_SECOND.get() and self.owner.items == 2:
                self._execute('SELECT 1 / 0 /* Chapter 10: second item failure */', ())
        return self._execute(sql, parameters)

    def _execute(self, sql, parameters):
        entry = dict(sql=sql, parameters=[serial(p) for p in parameters])
        try:
            self.raw.execute(sql, parameters)
            record('SQL', **entry)
        except Exception as exc:
            record('DB 오류', **entry, sqlstate=sqlstate(exc))
            raise
        return self

    def fetchone(self):
        return self.raw.fetchone()

    def fetchall(self):
        return self.raw.fetchall()

    def close(self):
        self.raw.close()


class ObservedConnection:
    def __init__(self):
        self.raw = dedicated_connection()
        self.items = 0

    def cursor(self):
        return ObservedCursor(self)

    def commit(self):
        self.raw.commit()
        record('COMMIT')

    def rollback(self):
        self.raw.rollback()
        record('ROLLBACK')

    def close(self):
        self.raw.close()
        record('CLOSE')


def snapshot():
    """A new connection and one repeatable-read snapshot for all displayed values."""
    conn = dedicated_connection()
    try:
        with closing(conn.cursor()) as cur:
            cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            counts = {}
            for table in TABLES:  # fixed internal names, never user-supplied SQL
                cur.execute(f'SELECT COUNT(*) FROM {table}')
                counts[table] = cur.fetchone()[0]
            cur.execute('''SELECT p.product_id::text, p.product_name,
                COALESCE(SUM(l.quantity_change),0) FROM products p
                LEFT JOIN stock_ledger l USING (product_id)
                GROUP BY p.product_id,p.product_name ORDER BY p.product_id''')
            stock = [dict(product_id=r[0], name=r[1], quantity=r[2]) for r in cur.fetchall()]
            cur.execute('''SELECT o.order_id::text,o.order_status,p.product_name,
                i.quantity,i.price_snapshot FROM orders o
                LEFT JOIN order_items i USING (order_id)
                LEFT JOIN products p USING (product_id)
                ORDER BY o.created_at,o.order_id,i.order_item_id''')
            orders = [dict(order_id=r[0], status=r[1], name=r[2], quantity=r[3],
                           price=serial(r[4])) for r in cur.fetchall()]
            cur.execute('SELECT price FROM product_prices WHERE product_price_id=%s', (PRICE,))
            price = cur.fetchone()
        conn.rollback()
        return dict(counts=counts, stock=stock, orders=orders,
                    current_price=serial(price[0]) if price else None,
                    source='요청 종료 후 새 연결 · 동일 시점 읽기')
    finally:
        conn.close()


def change_price(value):
    if value not in (5000, 6000):
        raise ValueError('Only fixed lab prices are allowed')
    conn = dedicated_connection()
    try:
        with closing(conn.cursor()) as cur:
            cur.execute('UPDATE product_prices SET price=%s WHERE product_price_id=%s RETURNING price',
                        (value, PRICE))
            if not cur.fetchone():
                raise RuntimeError('Seed price missing')
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
