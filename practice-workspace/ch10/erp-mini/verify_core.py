"""Fixed independent checks, using a new schema, never resetting learner tables.

Run: python verify_core.py --allow-test-writes
Only the generated ch10_verify_<UUID> schema is created and removed.
"""
import argparse
from contextlib import closing
from pathlib import Path
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
import lab_app
import lab_store as store


def verify(verbosity=2):
    base = store.raw_connection
    schema = 'ch10_verify_' + uuid4().hex

    def connect():
        conn = base()
        with closing(conn.cursor()) as cur:
            cur.execute(f'SET search_path TO {schema}')
        conn.commit()
        return conn

    conn = base()
    try:
        with closing(conn.cursor()) as cur:
            cur.execute(f'CREATE SCHEMA {schema}')
        conn.commit()
    finally:
        conn.close()
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

        def request(items=None):
            return dict(corp_id=store.COMPANY, items=items if items is not None else [
                dict(product_id=store.RAMEN, quantity=2), dict(product_id=store.COLA, quantity=1)])

        class Checks(unittest.TestCase):
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

            def test_02_actual_db_failure_and_no_partial_writes(self):
                before = store.snapshot()
                r = client.post('/orders', json=request(), headers={'X-Lab-Fail-Second': 'yes'})
                self.assertEqual(r.status_code, 500)
                self.assertEqual(before, store.snapshot())
                trace = r.json()['observation']['trace']
                error = next(i for i, e in enumerate(trace) if e['action'] == 'DB 오류')
                self.assertEqual(trace[error]['sqlstate'], '22012')
                self.assertTrue(any('INSERT INTO stock_ledger' in e.get('sql', '') for e in trace[:error]))
                self.assertTrue(any(e['action'] == 'ROLLBACK' for e in trace[error:]))
                self.assertFalse(any(e['action'] == 'COMMIT' for e in trace))

            def test_03_price_snapshot_and_restore(self):
                old = store.snapshot()['orders']
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

        result = unittest.TextTestRunner(verbosity=verbosity).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
        return result.wasSuccessful()
    finally:
        store.raw_connection = base
        conn = base()
        try:
            with closing(conn.cursor()) as cur:
                cur.execute(f'DROP SCHEMA {schema} CASCADE')
            conn.commit()
        finally:
            conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-test-writes', action='store_true')
    args = parser.parse_args()
    if not args.allow_test_writes:
        parser.error('Use --allow-test-writes to create/drop ONLY a generated ch10_verify_<UUID> schema.')
    try:
        raise SystemExit(0 if verify() else 1)
    except Exception as exc:
        print(f'NOT RUN: isolated PostgreSQL checks unavailable ({type(exc).__name__}). No connection values printed.')
        raise SystemExit(2)
