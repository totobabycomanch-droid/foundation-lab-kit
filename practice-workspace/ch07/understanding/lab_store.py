"""제공 사례 준비·실제 SQLite 실행 추적·새 연결 조회. 업무 트랜잭션은 학습자 책임."""
from pathlib import Path
from uuid import uuid4
import re
import sqlite3
from lab_contracts import LabError


class Result:
    def __init__(self, rows, rowcount, lastrowid):
        self.rows = rows
        self.rowcount, self.lastrowid = rowcount, lastrowid
    def fetchone(self):
        return dict(self.rows[0]) if self.rows else None
    def fetchall(self):
        return [dict(r) for r in self.rows]


class TraceDB:
    def __init__(self, path, trace, phase):
        self.raw = sqlite3.connect(path, timeout=5)
        self.raw.row_factory = sqlite3.Row
        self.trace, self.phase, self.active = trace, phase, None
        self.raw.set_trace_callback(self._observed)
        self.execute('PRAGMA foreign_keys = ON')
    @property
    def in_transaction(self):
        return self.raw.in_transaction
    def _observed(self, sql):
        if self.active is None:
            self.trace.append(dict(step=len(self.trace)+1, phase=self.phase, sql=sql, parameters=[], executed_sql=[sql], rows=[], affected_rows=None, error=None))
        else:
            self.active['executed_sql'].append(sql)
    def execute(self, sql, parameters=()):
        entry = dict(step=len(self.trace)+1, phase=self.phase, sql=sql, parameters=list(parameters), executed_sql=[], rows=[], affected_rows=None, error=None)
        self.trace.append(entry);self.active=entry
        try:
            cur=self.raw.execute(sql,tuple(parameters))
            rows=[dict(r) for r in cur.fetchall()] if cur.description else []
            entry['rows']=rows;entry['affected_rows']=cur.rowcount if cur.rowcount>=0 else None
            return Result(rows,cur.rowcount,cur.lastrowid)
        except Exception as error:
            entry.update(error=type(error).__name__,error_detail=str(error),sqlite_errorcode=getattr(error,'sqlite_errorcode',None),sqlite_errorname=getattr(error,'sqlite_errorname',None))
            raise
        finally:self.active=None
    def commit(self):self.raw.commit()
    def rollback(self):self.raw.rollback()
    def __enter__(self):
        self.raw.__enter__();return self
    def __exit__(self,*args):return self.raw.__exit__(*args)
    def close(self):self.raw.close()


def integer(value, minimum=1):
    if type(value) is not int or not minimum<=value<=1000000:
        raise LabError(422,'수량은 허용 범위의 정수로 입력하세요. 판매 수량은 1 이상입니다.')
    return value


def prepare(path, initial, kind, trace):
    db=TraceDB(path,trace,'실습 데이터 준비')
    try:
        db.execute('DROP TRIGGER IF EXISTS lab_fail_sale')
        db.execute('DROP TABLE IF EXISTS sales');db.execute('DROP TABLE IF EXISTS orders');db.execute('DROP TABLE IF EXISTS stock')
        db.execute('CREATE TABLE stock (prod_code TEXT PRIMARY KEY, qty INTEGER NOT NULL CHECK(qty>=0))')
        if kind=='sale':
            db.execute('''CREATE TABLE sales (id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_key TEXT NOT NULL UNIQUE, prod_code TEXT NOT NULL REFERENCES stock(prod_code),
                qty INTEGER NOT NULL CHECK(typeof(qty)='integer' AND qty>0))''')
        else:db.execute('CREATE TABLE orders (id INTEGER PRIMARY KEY, qty INTEGER NOT NULL CHECK(qty>0))')
        db.execute('INSERT INTO stock VALUES (?,?)',('A001',initial))
        if kind=='sale':db.execute('INSERT INTO stock VALUES (?,?)',('B001',initial))
        db.commit()
    finally:db.close()


def snapshot(path, kind, trace):
    db=TraceDB(path,trace,'저장 후 재조회 · 새 연결')
    try:
        db.execute('BEGIN')
        stock=db.execute('SELECT prod_code, qty FROM stock ORDER BY prod_code').fetchall()
        if kind=='sale':
            sales=db.execute('SELECT id, request_key, prod_code, qty FROM sales ORDER BY id').fetchall()
            fail=db.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name='lab_fail_sale'").fetchall()
            result=dict(stock=stock,sales=sales,sales_count=len(sales),failure_enabled=bool(fail))
        else:
            orders=db.execute('SELECT id,qty FROM orders ORDER BY id').fetchall()
            result=dict(stock=stock,orders=orders,orders_count=len(orders))
        db.commit();return result
    finally:db.close()


class Store:
    def __init__(self, root):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
    def session_path(self, session):
        if not isinstance(session,str) or not re.fullmatch('[0-9a-f]{32}',session):raise LabError(422,'실습 세션을 다시 여세요.')
        p=self.root/session
        if not p.is_dir():raise LabError(404,'실습 세션이 없습니다. 화면을 새로 열어 주세요.')
        return p
    def new_session(self, trace):
        key=uuid4().hex;p=self.root/key;p.mkdir()
        prepare(p/'sale.sqlite3',5,'sale',trace)
        return key,snapshot(p/'sale.sqlite3','sale',trace)
    def observe(self, session, trace):return snapshot(self.session_path(session)/'sale.sqlite3','sale',trace)
    def reset_sale(self, session, initial, trace):
        p=self.session_path(session)/'sale.sqlite3'
        prepare(p,integer(initial,0),'sale',trace);return snapshot(p,'sale',trace)
    def failure(self, session, enabled, trace):
        if type(enabled) is not bool:raise LabError(422,'실패 장치는 켜기·끄기로 지정하세요.')
        p=self.session_path(session)/'sale.sqlite3';db=TraceDB(p,trace,'실습 전용 저장 실패 장치')
        try:
            db.execute('DROP TRIGGER IF EXISTS lab_fail_sale')
            if enabled:db.execute("CREATE TRIGGER lab_fail_sale BEFORE INSERT ON sales BEGIN SELECT RAISE(ABORT,'intentional sale storage failure'); END")
            db.commit()
        finally:db.close()
        return snapshot(p,'sale',trace)
    def compare(self, session, initial, quantity, run):
        initial=integer(initial);quantity=integer(quantity)
        if quantity>initial:raise LabError(422,'비교할 처리 수량은 초기 재고 이하여야 합니다.')
        result=[];folder=self.session_path(session)
        for early in (True,False):
            trace=[];p=folder/('early.sqlite3' if early else 'atomic.sqlite3')
            prepare(p,initial,'order',trace)
            db=TraceDB(p,trace,'업무 처리 · 중간 확정' if early else '업무 처리 · 함께 취소')
            status,detail=500,'의도한 주문 저장 실패를 확인하지 못했습니다.'
            error_name=None;unfinished=False
            try:
                run(db,quantity,early)
            except LabError as error:status,detail=error.status,error.detail
            except sqlite3.IntegrityError as error:
                error_name=type(error).__name__
                if any(t['sql'].lstrip().upper().startswith('INSERT INTO ORDERS') and t['error']=='IntegrityError' and 'CHECK constraint failed' in t.get('error_detail','') for t in trace):
                    status,detail=200,'실제 주문 저장 오류 뒤 DB를 다시 조회했습니다.'
                else:detail='예상과 다른 DB 오류입니다: '+str(error)
            except Exception as error:detail='처리에 실패했습니다: '+type(error).__name__
            finally:
                unfinished=db.in_transaction
                if unfinished:
                    db.phase='미완료 거래 정리 · 학습자 롤백 아님';db.rollback()
                    status,detail=500,'업무 코드가 거래를 끝내지 않았습니다. 제공 기반의 정리를 구현 성공으로 보지 마세요.'
                db.close()
            result.append(dict(label='중간 확정 후 실패' if early else '함께 취소한 실패',status_code=status,detail=detail,
                storage_error=error_name,unfinished=unfinished,trace=trace,snapshot=snapshot(p,'order',trace)))
        return result
    def sale(self, session, key, product, quantity, sell, trace):
        p=self.session_path(session)/'sale.sqlite3'
        if not isinstance(key,str) or not key.strip() or len(key)>100:raise LabError(422,'요청 키를 확인하세요.')
        if product not in ('A001','B001'):raise LabError(422,'상품을 확인하세요.')
        integer(quantity)
        db=TraceDB(p,trace,'판매 업무 처리')
        status,detail,outcome,number=200,'판매 요청을 처리했습니다.','확정',None
        try:
            number=sell(db,key,product,quantity)
            if type(number) is not int:raise ValueError('판매번호는 정수여야 합니다.')
        except LabError as error:status,detail,outcome=error.status,error.detail,'거부'
        except Exception as error:
            status,detail,outcome=500,'저장 오류: '+str(error),'취소'
        finally:
            if db.in_transaction:
                db.phase='미완료 거래 정리 · 학습자 롤백 아님';db.rollback()
                status,detail,outcome=500,'업무 코드가 거래를 끝내지 않았습니다. 확정·취소 위치를 확인하세요.','미완료'
            db.close()
        if status>=400:number=None
        return status,detail,outcome,number,snapshot(p,'sale',trace)
