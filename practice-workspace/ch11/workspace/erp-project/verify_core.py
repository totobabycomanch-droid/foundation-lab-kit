"""생성 코드와 독립된 ch11 업무 검사. 독자용 A·B를 승인·초기화하지 않는다."""
import argparse
import json
import shutil
import subprocess
import sys
import uuid
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

import lab_db as db
import lab_servers as servers

DB_CHECKS = ('db.normal', 'db.shortage', 'db.reapproval', 'db.mid_failure',
             'db.reader_preserved', 'db.test_rows_rolled_back')
HTTP_CHECKS = ('http.query', 'http.normal', 'http.shortage', 'http.reapproval',
               'http.test_rows_removed', 'http.reader_preserved')


class RollbackOnly(Exception):
    pass


def reason(error):
    return str(error) if isinstance(error, db.LabError) else type(error).__name__


def add(report, name, status, detail=None):
    report[name] = {'result': status}
    if detail:
        report[name]['reason'] = detail


def reader_snapshot(cur):
    cur.execute('SELECT to_jsonb(o),to_jsonb(s),COALESCE('
                '(SELECT jsonb_agg(to_jsonb(l) ORDER BY l.ledger_id) FROM public.stock_ledger l '
                "WHERE l.order_id=o.order_id),'[]'::jsonb) FROM public.orders o "
                'JOIN public.stock s ON s.product_id=o.product_id WHERE o.order_id IN (%s,%s) ORDER BY o.order_id',
                (db.CASES['A'][0], db.CASES['B'][0]))
    return cur.fetchall()


def fixture(stock, name):
    token = uuid.uuid4().hex
    return {'id': str(uuid.uuid4()), 'product': 'CH11-TEST-' + token,
            'name': '자동 검사 ' + name, 'stock': stock}


def seed(cur, item):
    cur.execute('INSERT INTO public.stock(product_id,product_name,quantity,corp_id) VALUES (%s,%s,%s,%s)',
                (item['product'], item['name'], item['stock'], 'HQ'))
    cur.execute('INSERT INTO public.orders(order_id,order_name,product_id,quantity,corp_id) VALUES (%s,%s,%s,3,%s)',
                (item['id'], item['name'], item['product'], 'HQ'))


def stored(cur, item):
    cur.execute('SELECT o.status,s.quantity,COUNT(l.ledger_id)::int,SUM(l.qty_change)::int '
                'FROM public.orders o JOIN public.stock s ON s.product_id=o.product_id '
                'LEFT JOIN public.stock_ledger l ON l.order_id=o.order_id '
                'WHERE o.order_id=%s GROUP BY o.order_id,o.status,s.quantity', (item['id'],))
    row = cur.fetchone()
    return tuple(row) if row else None


def approve(cur, item):
    cur.execute('SELECT public.approve_order(%s::uuid,%s::varchar,3)', (item['id'], item['product']))


def rejected(cur, item, code=None):
    cur.execute('SAVEPOINT ch11_reject')
    try:
        approve(cur, item)
    except Exception as error:
        cur.execute('ROLLBACK TO SAVEPOINT ch11_reject')
        cur.execute('RELEASE SAVEPOINT ch11_reject')
        actual = getattr(error, 'pgcode', '') or ''
        valid = actual == code if code else actual.startswith(('P0', 'P1', '23'))
        assert valid
        return
    cur.execute('RELEASE SAVEPOINT ch11_reject')
    raise AssertionError('approval_not_rejected')


def db_case(cur, kind, item):
    seed(cur, item)
    if kind == 'normal':
        approve(cur, item)
        assert stored(cur, item) == ('PAID', 7, 1, -3)
    elif kind == 'shortage':
        rejected(cur, item)
        assert stored(cur, item) == ('CREATED', 2, 0, None)
    elif kind == 'reapproval':
        approve(cur, item)
        assert stored(cur, item) == ('PAID', 7, 1, -3)
        rejected(cur, item)
        assert stored(cur, item) == ('PAID', 7, 1, -3)
    else:
        # 이 트랜잭션에서만 검사 주문의 원장 INSERT를 막는다. 기존 행은 검사하지 않는다.
        constraint = 'ch11_test_' + uuid.uuid4().hex
        cur.execute(f'ALTER TABLE public.stock_ledger ADD CONSTRAINT {constraint} '
                    f"CHECK (order_id <> '{item['id']}'::uuid) NOT VALID")
        rejected(cur, item, '23514')
        assert stored(cur, item) == ('CREATED', 10, 0, None)
        cur.execute(f'ALTER TABLE public.stock_ledger DROP CONSTRAINT {constraint}')


def no_fixture_rows(cur, items):
    for item in items:
        cur.execute('SELECT 1 FROM public.orders WHERE order_id=%s', (item['id'],))
        assert cur.fetchone() is None
        cur.execute('SELECT 1 FROM public.stock WHERE product_id=%s', (item['product'],))
        assert cur.fetchone() is None
        cur.execute('SELECT 1 FROM public.stock_ledger WHERE order_id=%s OR product_id=%s',
                    (item['id'], item['product']))
        assert cur.fetchone() is None


def run_database(report):
    items, before, preserved_during = [], None, False
    try:
        try:
            with db.connection() as cur:
                db.require_schema(cur)
                before = reader_snapshot(cur)
                for kind in ('normal', 'shortage', 'reapproval', 'mid_failure'):
                    item = fixture(2 if kind == 'shortage' else 10, kind)
                    items.append(item)
                    cur.execute('SAVEPOINT ch11_case')
                    try:
                        db_case(cur, kind, item)
                        add(report, 'db.' + kind, 'Pass')
                    except Exception as error:
                        cur.execute('ROLLBACK TO SAVEPOINT ch11_case')
                        add(report, 'db.' + kind, 'Fail', reason(error))
                    cur.execute('RELEASE SAVEPOINT ch11_case')
                preserved_during = reader_snapshot(cur) == before
                # 성공한 쓰기와 임시 제약까지 확정하지 않고 모두 취소한다.
                raise RollbackOnly()
        except RollbackOnly:
            pass
        with db.connection() as cur:
            db.require_schema(cur)
            preserved_after = reader_snapshot(cur) == before
            add(report, 'db.reader_preserved', 'Pass' if preserved_during and preserved_after else 'Fail')
            no_fixture_rows(cur, items)
            add(report, 'db.test_rows_rolled_back', 'Pass')
    except Exception as error:
        for name in DB_CHECKS:
            if name not in report:
                add(report, name, 'Not Run' if before is None else 'Fail', reason(error))


def request(method, endpoint, payload=None):
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = Request('http://127.0.0.1:8000' + endpoint, data=data, method=method,
                  headers={'Content-Type': 'application/json'})
    try:
        response = build_opener(ProxyHandler({})).open(req, timeout=20)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.loads(response.read(65536))


def current(item):
    with db.connection() as cur:
        db.require_schema(cur)
        return stored(cur, item)


def cleanup(cur, items):
    # 예상한 이름·소속·상품이 맞는 검사 데이터만 지운다. 다른 객체는 보존한다.
    for item in items:
        cur.execute('SELECT product_id,order_name,corp_id FROM public.orders WHERE order_id=%s FOR UPDATE', (item['id'],))
        row = cur.fetchone()
        assert row is None or tuple(row) == (item['product'], item['name'], 'HQ')
        cur.execute('SELECT product_name,corp_id FROM public.stock WHERE product_id=%s FOR UPDATE', (item['product'],))
        row = cur.fetchone()
        assert row is None or tuple(row) == (item['name'], 'HQ')
    for item in items:
        cur.execute('DELETE FROM public.stock_ledger WHERE order_id=%s', (item['id'],))
        cur.execute('DELETE FROM public.orders WHERE order_id=%s', (item['id'],))
        cur.execute('DELETE FROM public.stock WHERE product_id=%s', (item['product'],))


def run_http(report):
    before, attempted = None, False
    items = [fixture(10, 'http normal'), fixture(2, 'http shortage')]
    try:
        with db.connection() as cur:
            db.require_schema(cur)
            before = reader_snapshot(cur)
        # 다른 프로세스의 포트를 재사용하지 않는다. 실행 도구가 소유한 API만 사용한다.
        servers.start('api')
        status, body = request('GET', '/orders')
        assert len(before) == 2
        for row, case in zip(before, db.CASES.values()):
            assert (row[0]['order_id'], row[0]['product_id'], row[0]['order_name'],
                    row[1]['product_name'], row[0]['quantity']) == (case[0], case[1], case[2], case[3], 3)
        expected = [dict(order_id=row[0]['order_id'], order_name=row[0]['order_name'],
                         product_id=row[0]['product_id'], product_name=row[1]['product_name'],
                         qty=row[0]['quantity'], current_stock=row[1]['quantity'], status=row[0]['status'])
                    for row in before]
        assert status == 200 and len(expected) == 2 and body.get('items') == expected
        add(report, 'http.query', 'Pass')
        attempted = True
        with db.connection() as cur:
            db.require_schema(cur)
            for item in items:
                seed(cur, item)
        for kind, item, expected_status, expected_state in (
            ('normal', items[0], 200, ('PAID', 7, 1, -3)),
            ('shortage', items[1], 400, ('CREATED', 2, 0, None)),
            ('reapproval', items[0], 400, ('PAID', 7, 1, -3)),
        ):
            try:
                status, body = request('POST', '/orders/approve',
                                       {'order_id': item['id'], 'product_id': item['product'], 'qty': 3})
                assert status == expected_status
                if status == 200:
                    assert body.get('status') == 'success'
                else:
                    assert isinstance(body.get('detail'), str) and body['detail']
                assert current(item) == expected_state
                add(report, 'http.' + kind, 'Pass')
            except Exception as error:
                add(report, 'http.' + kind, 'Fail', reason(error))
    except Exception as error:
        for name in HTTP_CHECKS[:4]:
            if name not in report:
                add(report, name, 'Not Run' if before is None else 'Fail', reason(error))
    finally:
        if attempted:
            try:
                with db.connection() as cur:
                    db.require_schema(cur)
                    cleanup(cur, items)
                with db.connection() as cur:
                    no_fixture_rows(cur, items)
                add(report, 'http.test_rows_removed', 'Pass')
            except Exception as error:
                add(report, 'http.test_rows_removed', 'Fail', reason(error))
                report['http.test_rows_removed']['test_order_ids'] = [item['id'] for item in items]
        else:
            add(report, 'http.test_rows_removed', 'Not Run', 'http_fixtures_not_created')
        if before is not None:
            try:
                with db.connection() as cur:
                    db.require_schema(cur)
                    assert reader_snapshot(cur) == before
                add(report, 'http.reader_preserved', 'Pass')
            except Exception as error:
                add(report, 'http.reader_preserved', 'Fail', reason(error))
        else:
            add(report, 'http.reader_preserved', 'Not Run', 'database_not_ready')


def run_build(report):
    front = db.ROOT.parent / 'frontend-project'
    npm = shutil.which('npm.cmd' if sys.platform == 'win32' else 'npm')
    if not npm or not (front / 'node_modules/vite/bin/vite.js').is_file():
        add(report, 'build', 'Not Run', 'frontend_dependencies_missing')
        return
    try:
        result = subprocess.run([npm, 'run', 'build'], cwd=front, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=60,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        secrets = []
        try:
            secrets.append(db.settings()['password'])
        except db.LabError:
            pass
        log = servers.redact(result.stdout + result.stderr, secrets)
        (servers.runtime(db.ROOT) / 'build.log').write_text(log, encoding='utf-8')
        add(report, 'build', 'Pass' if result.returncode == 0 else 'Fail',
            None if result.returncode == 0 else 'see_sanitized_build_log')
    except Exception as error:
        add(report, 'build', 'Fail', reason(error))


def main(argv=None):
    if sys.flags.optimize:
        print(json.dumps({'checks': {'result': 'Not Run', 'reason': 'run_python_without_optimization'}}))
        return 1
    parser = argparse.ArgumentParser(description='Fixed ch11 checks; reader A/B are preserved')
    parser.add_argument('--only', action='append', choices=('db', 'http', 'build'))
    args = parser.parse_args(argv)
    selected = args.only or ['db', 'http', 'build']
    report = {}
    if 'db' in selected:
        run_database(report)
    if 'http' in selected:
        if 'db' in selected and any(report[name]['result'] != 'Pass' for name in DB_CHECKS):
            for name in HTTP_CHECKS:
                add(report, name, 'Not Run', 'database_checks_not_passed')
        else:
            run_http(report)
    if 'build' in selected:
        run_build(report)
    add(report, 'browser', 'Not Run', 'reader_screen_check_is_separate')
    add(report, 'concurrency', 'Not Run', 'optional_multi_connection_lab')
    required = [value for key, value in report.items() if key not in ('browser', 'concurrency')]
    print(json.dumps(report, ensure_ascii=False))
    return 0 if required and all(value['result'] == 'Pass' for value in required) else 1


if __name__ == '__main__':
    raise SystemExit(main())
