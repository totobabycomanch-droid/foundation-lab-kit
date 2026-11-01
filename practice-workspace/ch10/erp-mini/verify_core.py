"""Fixed independent checks, using a new schema, never resetting learner tables.

Run: python verify_core.py --allow-test-writes
Only the generated ch10_verify_<UUID> schema is created and removed.
"""
import argparse
from contextlib import closing
from pathlib import Path
import unittest
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import server
import lab_app
import lab_store as store


class VerificationUnavailable(RuntimeError):
    """DB 연결·임시 스키마 생성이 불가능해 실행하지 못한 경우입니다."""


def verify(verbosity=2):
    base = store.raw_connection
    schema = 'ch10_verify_' + uuid4().hex

    def connect():
        conn = base()
        with closing(conn.cursor()) as cur:
            cur.execute(f'SET search_path TO {schema}')
        conn.commit()
        return conn

    try:
        conn = base()
    except Exception:
        raise VerificationUnavailable('DB connection unavailable') from None
    try:
        with closing(conn.cursor()) as cur:
            cur.execute(f'CREATE SCHEMA {schema}')
        conn.commit()
    except Exception:
        raise VerificationUnavailable('temporary schema unavailable') from None
    finally:
        conn.close()
    previous_schema = store.VERIFY_SCHEMA
    store.VERIFY_SCHEMA = schema
    store.raw_connection = connect
    try:
        conn = connect()
        try:
            with closing(conn.cursor()) as cur:
                cur.execute("CREATE TABLE foundation_lab_marker(lab_id text PRIMARY KEY)")
                cur.execute("INSERT INTO foundation_lab_marker VALUES ('chapter10')")
                cur.execute(Path(__file__).with_name('schema.sql').read_text(encoding='utf-8-sig'))
                cur.execute((Path(__file__).parent / 'sql/10_seed.sql').read_text(encoding='utf-8-sig'))
            conn.commit()
        finally:
            conn.close()
        client = TestClient(lab_app.app)
        # 화면 서버의 오류 은닉 미들웨어를 통과하지 않고 주문 함수 자체를 호출합니다.
        raw_app = FastAPI()
        raw_app.post('/orders')(server.create_order)
        raw_client = TestClient(raw_app, raise_server_exceptions=False)

        def request(items=None):
            return dict(corp_id=store.COMPANY, items=items if items is not None else [
                dict(product_id=store.RAMEN, quantity=2), dict(product_id=store.COLA, quantity=1)])

        class Checks(unittest.TestCase):
            def setUp(self):
                """각 검사는 이번 실행의 임시 스키마에서 독립된 기초 데이터로 시작합니다."""
                conn = connect()
                try:
                    with closing(conn.cursor()) as cur:
                        names = ', '.join(f'{schema}.{table}' for table in sorted(store.READ_TABLES))
                        cur.execute(f'TRUNCATE TABLE {names} CASCADE')
                        cur.execute((Path(__file__).parent / 'sql/10_seed.sql').read_text(encoding='utf-8-sig'))
                    conn.commit()
                finally:
                    conn.close()

            def sql(self, statement, parameters=()):
                """검사용 고정 SQL만 임시 스키마에서 실행하고 조회값을 반환합니다."""
                conn = connect()
                try:
                    with closing(conn.cursor()) as cur:
                        cur.execute(statement, parameters)
                        rows = [tuple(row) for row in cur.fetchall()] if cur.description else []
                    conn.commit()
                    return rows
                finally:
                    conn.close()

            def test_01_normal_order(self):
                before = store.snapshot()
                r = client.post('/orders', json=request())
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.json()['status'], 'success')
                after = store.snapshot()
                for table, delta in zip(store.TABLES, [1, 2, 2, 1, 1]):
                    self.assertEqual(after['counts'][table] - before['counts'][table], delta, table)
                stock = {p['product_id']: p['quantity'] for p in after['stock']}
                self.assertEqual((stock[store.RAMEN], stock[store.COLA]), (98, 99))
                order = [o for o in after['orders'] if o['order_id'] == r.json()['order_id']]
                self.assertEqual({(o['name'], o['quantity'], o['price']) for o in order},
                    {('신라면 5입 팩', 2, '5000'), ('코카콜라 250ml', 1, '12000')})
                self.assertTrue(all(o['status'] == 'CREATED' for o in order))
                self.assertEqual(self.sql('SELECT order_id::text,event_type FROM order_events'),
                                 [(r.json()['order_id'], 'OrderCreated')])
                self.assertEqual(self.sql('SELECT order_id::text,from_status,to_status FROM order_state_history'),
                                 [(r.json()['order_id'], None, 'CREATED')])

            def test_02_actual_db_failure_and_no_partial_writes(self):
                before = store.snapshot()
                r = client.post('/orders', json=request(), headers={'X-Lab-Fail-Second': 'yes'})
                self.assertEqual(r.status_code, 500)
                self.assertEqual(before, store.snapshot())
                trace = r.json()['observation']['trace']
                error = next(i for i, e in enumerate(trace) if e['action'] == 'DB 오류')
                self.assertEqual(trace[error]['sqlstate'], '22012')
                writes = [store.inspect_order_sql(e['sql'], schema) for e in trace[:error]
                          if e['action'] == 'SQL']
                self.assertEqual(writes.count(('INSERT', 'order_items')), 1)
                self.assertEqual(writes.count(('INSERT', 'stock_ledger')), 1)
                self.assertLess(writes.index(('INSERT', 'order_items')), writes.index(('INSERT', 'stock_ledger')))
                self.assertTrue(any(e['action'] == 'ROLLBACK' for e in trace[error:]))
                self.assertFalse(any(e['action'] == 'COMMIT' for e in trace))
                self.assertEqual([e['action'] for e in trace if e['action'] in ('ROLLBACK','CLOSE')],
                                 ['ROLLBACK','CLOSE'])
                self.assertGreaterEqual(sum(e['action'] == 'CURSOR CLOSE' for e in trace),1)
                self.assertEqual(sum(e['action'] == 'CURSOR OPEN' for e in trace),
                                 sum(e['action'] == 'CURSOR CLOSE' for e in trace))

            def test_03_price_snapshot_and_restore(self):
                initial = client.post('/orders', json=request())
                self.assertEqual(initial.status_code, 200)
                old = store.snapshot()['orders']
                self.assertEqual(len(old), 2)
                try:
                    self.assertEqual(client.post('/lab/price', json={'price':6000}).status_code, 200)
                    r = client.post('/orders', json=request([dict(product_id=store.RAMEN, quantity=1)]))
                    self.assertEqual(r.status_code, 200)
                    new_id = r.json()['order_id']
                    self.assertEqual(client.post('/lab/price', json={'price':5000}).status_code, 200)
                    after = store.snapshot()
                    self.assertEqual(after['current_price'], '5000')
                    self.assertTrue(all(o in after['orders'] for o in old))
                    self.assertEqual([o['price'] for o in after['orders'] if o['order_id']==new_id], ['6000'])
                finally:
                    store.change_price(5000)

            def test_04_invalid_input_before_connection(self):
                before = store.snapshot()
                for items in ([], [dict(product_id=store.RAMEN,quantity=0)]):
                    r = client.post('/orders', json=request(items))
                    self.assertEqual(r.status_code, 422)
                    self.assertEqual(r.json()['observation']['trace'], [])
                self.assertEqual(before, store.snapshot())

            def test_05_missing_price_and_insufficient_stock(self):
                before = store.snapshot()
                for product, quantity in [('dddddddd-dddd-dddd-dddd-dddddddddddd',1), (store.RAMEN,1000)]:
                    r = client.post('/orders',json=request([dict(product_id=product,quantity=quantity)]))
                    self.assertEqual(r.status_code,400)
                    self.assertEqual(before,store.snapshot())

            def test_06_reload_and_read_do_not_write(self):
                before = store.snapshot()
                for _ in range(2):
                    self.assertEqual(client.get('/').status_code,200)
                    self.assertEqual(client.get('/lab/snapshot').json(),before)
                self.assertEqual(before,store.snapshot())

            def test_07_price_input_and_sanitized_error(self):
                self.assertEqual(client.post('/lab/price',json={'price':7000}).status_code,422)
                r = client.post('/orders',json=request(),headers={'X-Lab-Fail-Second':'yes'})
                self.assertNotIn('division by zero',r.json()['detail'])
                self.assertNotIn('DATABASE_URL',r.text)

            def test_08_changed_quantity(self):
                before = store.snapshot()
                r = client.post('/orders',json=request([dict(product_id=store.RAMEN,quantity=3)]))
                self.assertEqual(r.status_code,200)
                after = store.snapshot()
                stock = lambda s: next(p['quantity'] for p in s['stock'] if p['product_id']==store.RAMEN)
                self.assertEqual(stock(before)-stock(after),3)

            def test_09_order_api_sanitizes_its_own_db_error(self):
                token = store.TRACE.set([])
                failure = store.FAIL_SECOND.set(True)
                try:
                    before = store.snapshot()
                    r = raw_client.post('/orders', json=request())
                    self.assertEqual(r.status_code, 500)
                    self.assertEqual(before, store.snapshot())
                    self.assertIn('22012', [e.get('sqlstate') for e in store.TRACE.get()])
                    detail = r.json()['detail']
                    self.assertIsInstance(detail, str)
                    self.assertTrue(detail.strip())
                    for internal in ('division by zero', '22012', 'DATABASE_URL', 'password', 'Traceback', 'SELECT 1'):
                        self.assertNotIn(internal.lower(), detail.lower())
                finally:
                    store.FAIL_SECOND.reset(failure)
                    store.TRACE.reset(token)

            def test_10_only_current_effective_price_is_selected(self):
                self.sql("UPDATE product_prices SET valid_from=NOW()-INTERVAL '3 days' WHERE product_id=%s", (store.RAMEN,))
                self.sql("INSERT INTO product_prices(product_id,price,valid_from) VALUES (%s,9000,NOW()+INTERVAL '1 day')", (store.RAMEN,))
                self.sql("INSERT INTO product_prices(product_id,price,valid_from,valid_to) VALUES (%s,8000,NOW()-INTERVAL '1 day',NOW()-INTERVAL '1 hour')", (store.RAMEN,))
                r = client.post('/orders',json=request([dict(product_id=store.RAMEN,quantity=1)]))
                self.assertEqual(r.status_code,200)
                self.assertEqual(self.sql('SELECT price_snapshot FROM order_items'), [(5000,)])

            def test_11_other_schema_sql_is_rejected_before_execution(self):
                before = store.snapshot()
                with closing(store.ObservedConnection()) as conn:
                    with closing(conn.cursor()) as cur:
                        for sql in ("INSERT INTO public.orders(corp_id,order_status) VALUES (%s,'CREATED')",
                                    'SELECT * FROM public.orders', 'SET search_path TO public',
                                    'SELECT 1; DELETE FROM orders'):
                            with self.subTest(sql=sql), self.assertRaises(store.LabSQLRejected):
                                cur.execute(sql, (store.COMPANY,))
                    conn.rollback()
                self.assertEqual(before, store.snapshot())

            def test_12_success_confirms_once_and_closes(self):
                r = client.post('/orders',json=request())
                self.assertEqual(r.status_code,200)
                trace = r.json()['observation']['trace']
                actions = [e['action'] for e in trace]
                self.assertEqual(actions.count('COMMIT'),1)
                self.assertNotIn('ROLLBACK',actions)
                self.assertEqual(actions[-2:],['COMMIT','CLOSE'])
                self.assertGreaterEqual(actions.count('CURSOR CLOSE'),1)
                self.assertEqual(actions.count('CURSOR OPEN'),actions.count('CURSOR CLOSE'))
                writes = [store.inspect_order_sql(e['sql'], schema)[1] for e in trace if e['action']=='SQL']
                for table in store.TABLES:
                    self.assertIn(table,writes)

        result = unittest.TextTestRunner(verbosity=verbosity).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
        return result.wasSuccessful()
    finally:
        store.raw_connection = base
        store.VERIFY_SCHEMA = previous_schema
        conn = base()
        try:
            with closing(conn.cursor()) as cur:
                cur.execute(f'DROP SCHEMA {schema} CASCADE')
            conn.commit()
        finally:
            conn.close()


def main(argv=None):
    """독립 검사를 실행하고 통과 0·실패 1·환경 미실행 2를 반환합니다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-test-writes', action='store_true')
    args = parser.parse_args(argv)
    if not args.allow_test_writes:
        parser.error('Use --allow-test-writes to create/drop ONLY a generated ch10_verify_<UUID> schema.')
    try:
        return 0 if verify() else 1
    except VerificationUnavailable as exc:
        print(f'NOT RUN: isolated PostgreSQL checks unavailable ({type(exc).__name__}). No connection values printed.')
        return 2
    except Exception as exc:
        print(f'FAIL: verification setup or cleanup error ({type(exc).__name__}). No connection values printed.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
