"""Reference business tests: offline checks complement actual PostgreSQL checks."""
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
import server


def client():
    # Keep offline business tests independent of provided observation middleware.
    app = FastAPI()
    app.include_router(server.app.router)
    return TestClient(app)


class Cursor:
    def __init__(self, fail_second=False):
        self.calls = []
        self.last = ''
        self.items = 0
        self.fail_second = fail_second

    def execute(self, sql, params=()):
        self.last = sql
        self.calls.append((sql,params))
        if 'INSERT INTO order_items' in sql:
            self.items += 1
            if self.fail_second and self.items == 2:
                raise RuntimeError('test-only storage failure')

    def fetchone(self):
        return (5000,) if 'SELECT price' in self.last else (100,)

    def close(self):
        pass


class Connection:
    def __init__(self, fail_second=False):
        self.cur = Cursor(fail_second)
        self.commits = self.rollbacks = self.closed = 0

    def cursor(self):
        return self.cur

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed += 1


class OrderTests(unittest.TestCase):
    def request(self):
        return {'corp_id':'11111111-1111-1111-1111-111111111111', 'items':[
            {'product_id':'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','quantity':2},
            {'product_id':'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','quantity':1}]}

    def test_normal_snapshot_and_single_commit(self):
        conn = Connection()
        with patch.object(server,'get_connection',return_value=conn):
            r = client().post('/orders',json=self.request())
        self.assertEqual(r.status_code,200)
        self.assertEqual((conn.commits,conn.rollbacks,conn.closed),(1,0,1))
        details=[p for sql,p in conn.cur.calls if 'INSERT INTO order_items' in sql]
        self.assertEqual([p[-1] for p in details],[5000,5000])

    def test_failure_after_first_item_rolls_back(self):
        conn = Connection(True)
        with patch.object(server,'get_connection',return_value=conn):
            r = client().post('/orders',json=self.request())
        self.assertEqual(r.status_code,500)
        self.assertEqual((conn.commits,conn.rollbacks,conn.closed),(0,1,1))
        self.assertTrue(any('INSERT INTO stock_ledger' in sql for sql,_ in conn.cur.calls))
        self.assertNotIn('test-only',r.text)

    def test_invalid_items_do_not_open_connection(self):
        for items in ([], [{'product_id':'a','quantity':0}]):
            with patch.object(server,'get_connection') as connect:
                r=client().post('/orders',json={**self.request(),'items':items})
                self.assertEqual(r.status_code,422)
                connect.assert_not_called()


if __name__=='__main__':
    unittest.main()
