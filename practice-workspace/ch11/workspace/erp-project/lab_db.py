"""ch11 실행 도구의 DB 경계. 연결값과 DB 예외 전문은 출력하지 않는다."""
import hashlib
import re
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES = {
    'A': ('00000000-0000-0000-0000-000000000001', 'PROD-100',
          '정상 승인용 주문 A', '정상 확인용 상품', 10),
    'B': ('00000000-0000-0000-0000-000000000002', 'PROD-200',
          '재고 부족용 주문 B', '부족 확인용 상품', 2),
}
EXPECTED = {
    'stock': {'product_id', 'product_name', 'quantity', 'corp_id'},
    'orders': {'order_id', 'order_name', 'product_id', 'quantity', 'status', 'corp_id', 'created_at'},
    'stock_ledger': {'ledger_id', 'order_id', 'product_id', 'qty_change', 'reason', 'corp_id', 'created_at'},
}


class LabError(Exception):
    """비밀값이 없는 고정된 오류 코드만 호출자에게 전달한다."""


def settings(root=ROOT):
    from dotenv import dotenv_values
    # 다른 작업 폴더의 .env나 상속된 DATABASE_URL을 선택하지 않는다.
    values = dotenv_values(root / '.env', interpolate=False)
    url = values.get('DATABASE_URL') or ''
    ref = values.get('CH11_PROJECT_REF') or ''
    if not url or not re.fullmatch(r'[a-z0-9]{20}', ref):
        raise LabError('local_settings_required')
    return validate_target(url, ref)


def validate_target(url, ref):
    from sqlalchemy.engine import make_url
    try:
        parsed = make_url(url)
        host = (parsed.host or '').lower()
        direct = host == f'db.{ref}.supabase.co' and parsed.username == 'postgres'
        pooler = host.endswith('.pooler.supabase.com') and parsed.username == f'postgres.{ref}'
        if (parsed.drivername not in ('postgresql', 'postgresql+psycopg2')
                or not (direct or pooler) or parsed.database != 'postgres'
                or (parsed.port or 5432) != 5432 or not parsed.password
                or set(parsed.query) - {'sslmode'}):
            raise ValueError()
        if parsed.query.get('sslmode', 'require') not in ('require', 'verify-ca', 'verify-full'):
            raise ValueError()
        return dict(host=host, port=5432, user=parsed.username, password=parsed.password,
                    dbname='postgres', sslmode=parsed.query.get('sslmode', 'require'),
                    connect_timeout=10, application_name='chapter11-lab')
    except Exception:
        raise LabError('dedicated_target_mismatch') from None


@contextmanager
def connection(root=ROOT):
    import psycopg2
    params = settings(root)
    conn = psycopg2.connect(**params)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SET LOCAL statement_timeout = '15s'")
                cur.execute("SET LOCAL lock_timeout = '5s'")
                cur.execute('SET LOCAL search_path = public, pg_catalog')
                cur.execute('SET LOCAL standard_conforming_strings = on')
                cur.execute('SELECT current_database(), session_user')
                database, user = cur.fetchone()
                if database != 'postgres' or user not in ('postgres', params['user']):
                    raise LabError('connected_identity_mismatch')
                # 같은 DB에서 적용·데이터 준비가 겹치지 않게 한다.
                cur.execute('SELECT pg_advisory_xact_lock(11002026)')
                yield cur
    finally:
        conn.close()


def objects(cur):
    cur.execute("SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                "WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f','S')")
    return {row[0] for row in cur.fetchall()}


def require_marker(cur):
    cur.execute("SELECT to_regclass('public.foundation_lab_marker')")
    if cur.fetchone()[0] is None:
        raise LabError('marker_missing_run_init')
    cur.execute("SELECT 1 FROM public.foundation_lab_marker WHERE lab_id='chapter11'")
    if cur.fetchone() is None:
        raise LabError('marker_mismatch')


def initialize(cur):
    existing = objects(cur)
    if existing - {'foundation_lab_marker', 'ch11_sql_history'}:
        raise LabError('existing_objects_preserved')
    cur.execute("SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                "WHERE n.nspname='public' AND p.proname='approve_order'")
    if cur.fetchone():
        raise LabError('existing_function_preserved')
    if 'foundation_lab_marker' in existing:
        require_marker(cur)
    else:
        cur.execute('CREATE TABLE public.foundation_lab_marker '
                    '(lab_id TEXT PRIMARY KEY, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())')
        cur.execute("INSERT INTO public.foundation_lab_marker(lab_id) VALUES ('chapter11')")
    cur.execute('CREATE TABLE IF NOT EXISTS public.ch11_sql_history '
                '(file_name TEXT PRIMARY KEY, sha256 TEXT NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW())')


def statements(source):
    """문자열·함수 본문·주석을 제외한 최상위 SQL 토큰을 읽는다."""
    tokens, result, i = [], [], 0
    while i < len(source):
        if source.startswith('--', i):
            end = source.find('\n', i)
            i = len(source) if end < 0 else end + 1
        elif source.startswith('/*', i):
            depth, i = 1, i + 2
            while i < len(source) and depth:
                if source.startswith('/*', i):
                    depth, i = depth + 1, i + 2
                elif source.startswith('*/', i):
                    depth, i = depth - 1, i + 2
                else:
                    i += 1
            if depth:
                raise LabError('sql_unclosed_comment')
        elif source[i] in "\"'":
            escaped = (source[i] == "'" and i > 0 and source[i - 1] in 'eE'
                       and (i < 2 or not (source[i - 2].isalnum() or source[i - 2] == '_')))
            quote, i = source[i], i + 1
            while i < len(source):
                if source[i] == quote:
                    if i + 1 < len(source) and source[i + 1] == quote:
                        i += 2
                    else:
                        i += 1
                        break
                elif source[i] == '\\' and escaped:
                    i += 2
                else:
                    i += 1
            else:
                raise LabError('sql_unclosed_quote')
        elif source[i] == '$' and (match := re.match(r'\$(?:[a-zA-Z_][a-zA-Z_0-9]*)?\$', source[i:])):
            tag = match.group()
            end = source.find(tag, i + len(tag))
            if end < 0:
                raise LabError('sql_unclosed_function_body')
            i = end + len(tag)
        elif source[i] == ';':
            if tokens:
                result.append(tokens)
            tokens, i = [], i + 1
        elif match := re.match(r'[a-zA-Z_][a-zA-Z_0-9]*', source[i:]):
            tokens.append(match.group().upper())
            i += len(match.group())
        else:
            i += 1
    if tokens:
        result.append(tokens)
    return result


def sql_source(name, root=ROOT):
    base = (root / 'sql').resolve()
    path = (base / name).resolve()
    if path.parent != base or path.suffix.lower() != '.sql' or not path.is_file():
        raise LabError('sql_file_outside_backend_sql')
    source = path.read_text(encoding='utf-8-sig')
    # 검토한 스키마 파일용 도구이며 임의 SQL의 보안 샌드박스가 아니다.
    # 적용 이력과 DDL의 트랜잭션을 깨는 제어문·데이터 초기화는 받지 않는다.
    commands = statements(source)
    allowed = (['CREATE', 'TABLE'], ['CREATE', 'FUNCTION'], ['CREATE', 'OR', 'REPLACE', 'FUNCTION'],
               ['CREATE', 'INDEX'], ['CREATE', 'UNIQUE', 'INDEX'], ['ALTER', 'TABLE'], ['COMMENT', 'ON'])
    if not commands or any(not any(cmd[:len(prefix)] == prefix for prefix in allowed)
                           or set(cmd) & {'DROP', 'TRUNCATE', 'DELETE', 'COMMIT', 'ROLLBACK'} for cmd in commands):
        raise LabError('schema_ddl_only_no_transaction_control')
    return path.name, source, hashlib.sha256(source.encode('utf-8')).hexdigest()


def apply_sql(cur, name, source, digest):
    require_marker(cur)
    cur.execute("SELECT to_regclass('public.ch11_sql_history')")
    if cur.fetchone()[0] is None:
        raise LabError('history_missing_use_fresh_database')
    cur.execute('SELECT sha256 FROM public.ch11_sql_history WHERE file_name=%s', (name,))
    row = cur.fetchone()
    if row:
        if row[0] != digest:
            raise LabError('applied_sql_changed_use_new_file')
        return 'already_applied'
    cur.execute('SELECT COUNT(*) FROM public.ch11_sql_history')
    if cur.fetchone()[0] == 0 and objects(cur) - {'foundation_lab_marker', 'ch11_sql_history'}:
        raise LabError('untracked_objects_preserved')
    cur.execute(source)
    cur.execute('INSERT INTO public.ch11_sql_history(file_name,sha256) VALUES (%s,%s)', (name, digest))
    return 'applied'


def require_schema(cur):
    require_marker(cur)
    for table, fields in EXPECTED.items():
        cur.execute('SELECT column_name FROM information_schema.columns '
                    "WHERE table_schema='public' AND table_name=%s", (table,))
        if not fields <= {row[0] for row in cur.fetchall()}:
            raise LabError('schema_not_ready_existing_data_preserved')


def prepare_case(cur, key, reset=False):
    require_schema(cur)
    oid, pid, order_name, product_name, stock = CASES[key]
    cur.execute('SELECT product_id,quantity,order_name,corp_id FROM public.orders WHERE order_id=%s FOR UPDATE', (oid,))
    order = cur.fetchone()
    if order and order != (pid, 3, order_name, 'HQ'):
        raise LabError('case_identity_conflict')
    cur.execute('SELECT product_name,corp_id FROM public.stock WHERE product_id=%s FOR UPDATE', (pid,))
    product = cur.fetchone()
    if product and (product != (product_name, 'HQ') or not order):
        raise LabError('product_identity_conflict')
    cur.execute('SELECT 1 FROM public.orders WHERE product_id=%s AND order_id<>%s', (pid, oid))
    if cur.fetchone():
        raise LabError('product_shared_with_other_order')
    if order and not reset:
        return 'preserved'
    if reset:
        cur.execute('DELETE FROM public.stock_ledger WHERE order_id=%s', (oid,))
    if product:
        cur.execute('UPDATE public.stock SET quantity=%s WHERE product_id=%s', (stock, pid))
    else:
        cur.execute('INSERT INTO public.stock(product_id,product_name,quantity,corp_id) VALUES (%s,%s,%s,%s)',
                    (pid, product_name, stock, 'HQ'))
    if order:
        cur.execute("UPDATE public.orders SET status='CREATED' WHERE order_id=%s", (oid,))
    else:
        cur.execute('INSERT INTO public.orders(order_id,order_name,product_id,quantity,status,corp_id) '
                    "VALUES (%s,%s,%s,3,'CREATED','HQ')", (oid, order_name, pid))
    return 'reset' if reset else 'prepared'


def inspect(cur):
    require_marker(cur)
    cur.execute("SELECT to_regclass('public.ch11_sql_history')")
    history = []
    if cur.fetchone()[0]:
        cur.execute('SELECT file_name,sha256 FROM public.ch11_sql_history ORDER BY applied_at,file_name')
        history = [{'file': r[0], 'sha256': r[1]} for r in cur.fetchall()]
    return {'connection': 'Pass', 'marker': 'Pass', 'sql_history': history}


def state(cur):
    require_schema(cur)
    ids = tuple(row[0] for row in CASES.values())
    cur.execute('SELECT o.order_name,o.status,s.quantity,COUNT(l.ledger_id),SUM(l.qty_change) '
                'FROM public.orders o JOIN public.stock s ON s.product_id=o.product_id '
                'LEFT JOIN public.stock_ledger l ON l.order_id=o.order_id '
                'WHERE o.order_id IN (%s,%s) GROUP BY o.order_id,o.order_name,o.status,s.quantity ORDER BY o.order_id', ids)
    return [dict(zip(('order_name', 'status', 'current_stock', 'ledger_count', 'qty_change'), row))
            for row in cur.fetchall()]
