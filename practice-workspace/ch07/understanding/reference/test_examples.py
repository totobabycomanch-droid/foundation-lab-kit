"""선택 비교용 업무 테스트. 제공 검사 외에 대표 DB 상태를 단언한다."""
from pathlib import Path
import tempfile
import unittest
from lab_store import prepare, TraceDB, snapshot
from lab_contracts import LabError
from transaction_example import run_transaction
from sale_example import sell


class TransactionTests(unittest.TestCase):
    def test_failure_results(self):
        """두 독립 DB에서 실제 INSERT 오류 뒤 재고 9/10·주문 0을 확인한다."""
        import sqlite3
        with tempfile.TemporaryDirectory() as folder:
            for early,expected in ((True,9),(False,10)):
                path=Path(folder)/str(early);prepare(path,10,'order',[])
                db=TraceDB(path,[],'test')
                try:
                    with self.assertRaises(sqlite3.IntegrityError):run_transaction(db,1,early)
                    self.assertFalse(db.in_transaction)
                finally:db.close()
                state=snapshot(path,'order',[])
                self.assertEqual(state['stock'][0]['qty'],expected)
                self.assertEqual(state['orders_count'],0)


class SaleTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path=Path(self.folder.name)/'sale'
        prepare(self.path,5,'sale',[])
        self.db=TraceDB(self.path,[],'test')
        self.addCleanup(self.db.close)

    def state(self):
        return snapshot(self.path,'sale',[])

    def test_retry_and_conflict(self):
        """같은 번호뿐 아니라 실제 DB 상태도 보존되는지 확인한다."""
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'sale';prepare(path,5,'sale',[])
            db=TraceDB(path,[],'test')
            try:
                first=sell(db,'request-1','A001',2)
                before=snapshot(path,'sale',[])
                self.assertEqual(sell(db,'request-1','A001',2),first)
                self.assertEqual(snapshot(path,'sale',[]),before)
                with self.assertRaises(LabError):sell(db,'request-1','A001',3)
                self.assertEqual(snapshot(path,'sale',[]),before)
            finally:db.close()

    def test_conflicts_preserve_whole_database(self):
        """상품·수량만 바뀐 같은 키는 각각 거부하고 기존 행을 보존한다."""
        sell(self.db,'one','A001',2)
        before=self.state()
        for product,quantity in (('A001',3),('B001',2)):
            with self.subTest(product=product):
                with self.assertRaises(LabError) as error:sell(self.db,'one',product,quantity)
                self.assertEqual(error.exception.status,409)
                self.assertEqual(self.state(),before)

    def test_invalid_quantities_preserve_database(self):
        """HTTP를 거치지 않아도 업무 함수가 잘못된 수량을 거부한다."""
        before=self.state()
        for quantity in (0,-1,True,None,1.5,'2',1000001):
            with self.subTest(quantity=quantity):
                with self.assertRaises(LabError) as error:sell(self.db,'invalid','A001',quantity)
                self.assertEqual(error.exception.status,422)
                self.assertEqual(self.state(),before)
                self.assertFalse(self.db.in_transaction)

    def test_stock_boundaries(self):
        """부족한 6개는 보존하고 정확한 5개 판매는 재고 0이 된다."""
        before=self.state()
        with self.assertRaises(LabError) as error:sell(self.db,'too-many','A001',6)
        self.assertEqual(error.exception.status,409)
        self.assertEqual(self.state(),before)
        number=sell(self.db,'all','A001',5)
        self.assertEqual(self.state()['stock'][0]['qty'],0)
        self.assertEqual(self.state()['sales'],[{'id':number,'request_key':'all','prod_code':'A001','qty':5}])

    def test_different_keys_are_separate_sales(self):
        """다른 키로 두 번 판매하면 두 번호와 재고 1이 남는다."""
        one=sell(self.db,'one','A001',2);two=sell(self.db,'two','A001',2)
        self.assertNotEqual(one,two)
        self.assertEqual(self.state()['stock'][0]['qty'],1)
        self.assertEqual(len(self.state()['sales']),2)

    def test_unique_key_constraint(self):
        """함수를 우회한 중복 키 INSERT도 DB가 거부한다."""
        import sqlite3
        sell(self.db,'one','A001',2);before=self.state()
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db:self.db.execute('INSERT INTO sales(request_key,prod_code,qty) VALUES (?,?,?)',('one','A001',1))
        self.assertEqual(self.state(),before)

    def test_storage_failure_and_same_key_retry(self):
        """실제 저장 오류 뒤 차감·키가 취소되고 같은 요청이 성공한다."""
        import sqlite3
        self.db.execute("CREATE TEMP TRIGGER reject_sale BEFORE INSERT ON sales BEGIN SELECT RAISE(ABORT,'test storage failure'); END")
        before=self.state()
        with self.assertRaises(sqlite3.IntegrityError):sell(self.db,'retry','A001',2)
        self.assertEqual(self.state(),before)
        self.assertFalse(self.db.in_transaction)
        self.db.execute('DROP TRIGGER reject_sale')
        number=sell(self.db,'retry','A001',2)
        self.assertEqual(self.state()['stock'][0]['qty'],3)
        self.assertEqual(self.state()['sales'],[{'id':number,'request_key':'retry','prod_code':'A001','qty':2}])


if __name__=='__main__':unittest.main()
