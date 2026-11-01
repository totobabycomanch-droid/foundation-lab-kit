"""Provided PostgreSQL observation tools. Never commits learner business writes."""
from contextlib import closing
from contextvars import ContextVar
from decimal import Decimal
from uuid import UUID

from pglast import parse_sql

from db import get_connection as raw_connection

RAMEN = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
COLA = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
COMPANY = '11111111-1111-1111-1111-111111111111'
PRICE = '11111111-2222-3333-4444-555555555555'
TABLES = ('orders', 'order_items', 'stock_ledger', 'order_events', 'order_state_history')
TRACE = ContextVar('ch10_trace', default=None)
FAIL_SECOND = ContextVar('ch10_fail_second', default=False)
# 독립 검사만 임시 스키마를 지정합니다. 화면 실습은 public을 사용합니다.
VERIFY_SCHEMA = None
READ_TABLES = {'companies', 'products', 'product_prices', *TABLES}
SQL_NODES = {
    'SelectStmt', 'InsertStmt', 'RangeVar', 'ResTarget', 'ColumnRef',
    'A_Const', 'String', 'Integer', 'Float', 'Boolean', 'A_Star', 'ParamRef',
    'A_Expr', 'BoolExpr', 'NullTest', 'FuncCall', 'CoalesceExpr', 'SortBy',
    'TypeCast', 'TypeName', 'SQLValueFunction', 'Alias', 'SubLink', 'JoinExpr',
}


class LabSQLRejected(ValueError):
    """제공 관찰 기능이 지원하지 않는 SQL을 실행 전에 거절합니다."""


def inspect_order_sql(sql, schema='public'):
    """단일 SELECT/한 행 INSERT의 대상과 기능을 검사하고 작업·테이블을 반환합니다.

    값은 분석기에 전달하지 않습니다. 허용 목록 밖 SQL은 DB 실행 전에 거절하며,
    이 제한은 제공 연결을 사용하는 실습 규약이지 Python 보안 샌드박스는 아닙니다.
    """
    try:
        statements = parse_sql(sql.replace('%s', 'NULL'))
    except Exception:
        raise LabSQLRejected('SQL 구문을 확인하세요. 한 번에 SELECT 또는 한 행 INSERT만 지원합니다.') from None
    if len(statements) != 1:
        raise LabSQLRejected('여러 SQL 문장을 한 번에 실행할 수 없습니다.')
    tree = statements[0].stmt()
    kind = tree['@']
    if kind not in ('SelectStmt', 'InsertStmt'):
        raise LabSQLRejected('주문 업무는 SELECT와 INSERT만 사용하세요. 확정·취소는 연결 메서드를 사용합니다.')

    def check(value):
        if isinstance(value, (tuple, list)):
            for child in value:
                check(child)
        elif isinstance(value, dict):
            tag = value.get('@')
            if tag and tag not in SQL_NODES:
                raise LabSQLRejected('제공 관찰 기능이 지원하지 않는 SQL 형식입니다.')
            if tag == 'RangeVar':
                if (value.get('catalogname') or value.get('schemaname') not in (None, schema)
                        or value.get('relname') not in READ_TABLES):
                    raise LabSQLRejected('현재 실습 스키마의 제공 테이블만 사용하세요. public 등 다른 스키마는 검사 중 접근할 수 없습니다.')
            if tag == 'SelectStmt' and (value.get('intoClause') or value.get('withClause')):
                raise LabSQLRejected('SELECT INTO와 WITH는 이 실습에서 지원하지 않습니다.')
            if tag == 'InsertStmt':
                source = value.get('selectStmt') or {}
                if (value['relation']['relname'] not in TABLES
                        or len(source.get('valuesLists') or ()) != 1
                        or source.get('fromClause') or value.get('withClause')
                        or value.get('onConflictClause')):
                    raise LabSQLRejected('주문 관련 테이블에 품목별 한 행 INSERT를 사용하세요.')
            if tag == 'FuncCall':
                names = [part['sval'] for part in value['funcname']]
                if len(names) != 1 or names[0] not in {'sum', 'count', 'now', 'gen_random_uuid'}:
                    raise LabSQLRejected('실습에서 허용하지 않은 SQL 함수입니다.')
            if tag == 'TypeName':
                names = [part['sval'] for part in value['names']]
                if (names[-1] not in {'uuid', 'text', 'int2', 'int4', 'int8', 'numeric',
                                      'timestamp', 'timestamptz', 'bool', 'float8'}
                        or len(names) > 2 or (len(names) == 2 and names[0] != 'pg_catalog')):
                    raise LabSQLRejected('실습에서 허용하지 않은 SQL 자료형입니다.')
            if tag == 'A_Expr':
                names = [part['sval'] for part in value.get('name') or ()]
                if len(names) != 1 or names[0] not in {'=', '<>', '!=', '<', '>', '<=', '>=', '+', '-', '*', '/'}:
                    raise LabSQLRejected('실습에서 허용하지 않은 SQL 연산자입니다.')
            for child in value.values():
                check(child)

    check(tree)
    return ('INSERT', tree['relation']['relname']) if kind == 'InsertStmt' else ('SELECT', None)


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
        try:
            action, table = inspect_order_sql(sql, VERIFY_SCHEMA or 'public')
        except LabSQLRejected as exc:
            record('SQL 차단', reason=str(exc))
            raise
        if action == 'INSERT' and table == 'order_items':
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
        record('CURSOR CLOSE')


class ObservedConnection:
    def __init__(self):
        self.raw = dedicated_connection()
        self.items = 0

    def cursor(self):
        cursor = ObservedCursor(self)
        record('CURSOR OPEN')
        return cursor

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
