"""제공 기능: 실습 2 전용 DB·실제 삭제 오류·추적·저장 후 별도 연결 조회."""
from pathlib import Path
from threading import Lock
import sqlite3
from .store import TracedDB
from .contracts import MovementError


class RelationshipStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.gate = Lock()
        with sqlite3.connect(self.path) as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS lab_product (
                    id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0 CHECK(is_deleted IN (0,1)));
                CREATE TABLE IF NOT EXISTS lab_trade (
                    id INTEGER PRIMARY KEY, trade_no TEXT NOT NULL UNIQUE,
                    product_id INTEGER NOT NULL REFERENCES lab_product(id) ON DELETE RESTRICT,
                    quantity INTEGER NOT NULL CHECK(typeof(quantity)='integer' AND quantity > 0));
            ''')

    def snapshot(self, read, trace):
        db = TracedDB(self.path, trace, '저장 후 재조회')
        try:
            db.execute('BEGIN')
            products = db.execute('SELECT id, code, name, is_deleted FROM lab_product ORDER BY code').fetchall()
            raw_trades = db.execute('SELECT trade_no, product_id, quantity FROM lab_trade ORDER BY trade_no').fetchall()
            try:
                views = read(db)
                if set(views) != {'selection', 'trades'}:
                    raise ValueError('Expected selection and trades')
                if not isinstance(views['selection'], list) or not isinstance(views['trades'], list):
                    raise ValueError('Expected query row lists')
                ready, issue = True, None
            except MovementError as error:
                if error.status != 501:
                    raise
                views = {'selection': None, 'trades': None}
                ready, issue = False, error.detail
            db.execute('COMMIT')
            return dict(products=products, raw_trades=raw_trades, **views, read_ready=ready, read_issue=issue)
        finally:
            db.close()

    def run(self, action, data, change, read, trace):
        with self.gate:
            status, detail, outcome = 200, 'DB에서 다시 조회했습니다.', '조회'
            if action != 'state':
                db = TracedDB(self.path, trace, '실습 2 ' + action)
                try:
                    db.execute('BEGIN IMMEDIATE')
                    if action == 'prepare':
                        if db.execute('SELECT id FROM lab_product LIMIT 1').fetchone():
                            raise MovementError(409, '이미 준비한 데이터가 있습니다. 다시 시작하려면 실습 2 초기화를 누르세요.')
                        db.execute('INSERT INTO lab_product (code,name) VALUES (?,?)', (data['code'],data['name']))
                        product = db.execute('SELECT id FROM lab_product WHERE code = ?', (data['code'],)).fetchone()
                        db.execute('INSERT INTO lab_trade (trade_no,product_id,quantity) VALUES (?,?,?)', ('T-0001',product['id'],data['quantity']))
                        detail = '상품과 거래를 함께 준비했습니다.'
                    elif action == 'reset':
                        db.execute('DELETE FROM lab_trade')
                        db.execute('DELETE FROM lab_product')
                        detail = '실습 2의 상품과 거래만 초기화했습니다.'
                    else:
                        referenced = None
                        if action == 'delete':
                            referenced = db.execute('''SELECT t.trade_no, t.quantity FROM lab_trade t
                                JOIN lab_product p ON p.id=t.product_id WHERE p.code=? ORDER BY t.trade_no''', (data['code'],)).fetchall()
                        change(db, data['code'], action)
                        if referenced:
                            raise MovementError(500, '검사 실패: 거래가 있는 상품의 실제 DB 삭제 차단을 확인하지 못했습니다.')
                        detail = '상품을 삭제했습니다.' if action == 'delete' else '취급을 중단했습니다. 예전 거래는 유지합니다.'
                    db.execute('COMMIT')
                    outcome = '확정'
                except Exception as error:
                    if db.connection.in_transaction:
                        db.execute('ROLLBACK')
                    outcome = '취소'
                    # RESTRICT raises SQLITE_CONSTRAINT_TRIGGER in SQLite. Do not
                    # misclassify arbitrary IntegrityError/trigger failures as FK.
                    failed_delete = any(t['error'] == 'IntegrityError' and t['sql'].lstrip().upper().startswith('DELETE FROM LAB_PRODUCT') for t in trace)
                    if action == 'delete' and failed_delete and isinstance(error, sqlite3.IntegrityError) and str(error) == 'FOREIGN KEY constraint failed':
                        status, detail = 409, '거래가 있는 상품은 삭제할 수 없습니다.'
                    elif isinstance(error, MovementError):
                        status, detail = error.status, error.detail
                    else:
                        status, detail = 500, '처리에 실패했습니다. 실제 SQL 상세와 AI 검증으로 확인하세요.'
                finally:
                    db.close()
            try:
                snapshot = self.snapshot(read, trace)
                if status == 200 and not snapshot['read_ready']:
                    detail += ' ' + snapshot['read_issue']
            except Exception:
                snapshot = None
                if status == 200:
                    status, detail = 500, '처리 후 조회에 실패했습니다. 저장 결과를 확인하기 전 같은 작업을 다시 보내지 마세요.'
                # Keep outcome: a committed write is not a rollback if read fails.
            return status, detail, outcome, snapshot
