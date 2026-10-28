"""실습 2를 임시 사본·서버·DB에서 검사한다. 사용 중인 DB는 변경하지 않는다."""
from contextlib import closing
import sqlite3
from verify_web import isolated, request, database


def main():
    passed = []
    def check(label, condition):
        assert condition, label
        passed.append(label); print('PASS', label, flush=True)
    try:
        with isolated() as (work, port):
            def call(action, body=None):
                return request(port, '/api/relationships/' + action, body if action != 'state' else None)
            def observe():
                status, r = call('state')
                assert status == 200 and r['snapshot']['read_ready'], 'Complete relationship_read.py first'
                return r['snapshot']
            def rows():
                with closing(sqlite3.connect(work/'.lab/relationships.sqlite3')) as db:
                    return [db.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in ('lab_product','lab_trade')]
            body = {'code':'A001', 'name':'샘플 상품', 'quantity':5}
            before_stock = database(work)
            empty = observe()
            check('starts with no products or trades', not empty['products'] and not empty['selection'] and not empty['trades'])
            status, ready = call('prepare', body)
            s = ready['snapshot']
            check('prepares actual product and trade together', status==200 and len(s['products'])==1 and s['trades']==[{'trade_no':'T-0001','code':'A001','name':'샘플 상품','quantity':5,'is_deleted':0}])
            check('active product appears in selection', s['selection']==[{'code':'A001','name':'샘플 상품'}])
            original = rows()
            status, duplicate = call('prepare', body)
            check('duplicate preparation preserves data', status==409 and rows()==original)
            status, denied = call('delete', {'code':'A001'})
            write = [t for t in denied['trace'] if t['phase']=='실습 2 delete']
            check('referenced product deletion is rejected', status==409 and denied['outcome']=='취소' and rows()==original)
            failed = [t for t in write if t['sql'].upper().startswith('DELETE FROM LAB_PRODUCT') and t['error']=='IntegrityError']
            check('actual DELETE fails with foreign key error', bool(failed) and failed[0]['error_detail']=='FOREIGN KEY constraint failed' and bool(failed[0]['executed_sql']))
            check('failed deletion rolls back then rereads', any(t['sql']=='ROLLBACK' for t in write) and not any(t['sql']=='COMMIT' for t in write) and denied['snapshot']['trades']==s['trades'])
            status, stopped = call('discontinue', {'code':'A001'})
            s = stopped['snapshot']
            check('discontinued product leaves selection', status==200 and not s['selection'])
            check('product row and old trade are preserved', len(s['products'])==1 and s['products'][0]['is_deleted']==1 and s['trades']==[{'trade_no':'T-0001','code':'A001','name':'샘플 상품','quantity':5,'is_deleted':1}])
            check('actual update and JOIN observed', any(t['sql'].upper().startswith('UPDATE LAB_PRODUCT') and t['parameters'] for t in stopped['trace']) and any('JOIN' in t['sql'].upper() and t['phase']=='저장 후 재조회' for t in stopped['trace']))
            check('request IDs are distinct', len({ready['request_id'],denied['request_id'],stopped['request_id']})==3)
            check('repeated discontinue preserves trade', call('discontinue', {'code':'A001'})[0]==200 and observe()['trades']==s['trades'])
            check('missing product is rejected', call('delete', {'code':'MISSING'})[0]==404)
            for q in (0,-1,1.5,'5',True,None,1000001):
                before = rows(); status, invalid = call('prepare', dict(body, quantity=q))
                check('invalid quantity '+repr(q), status==422 and not invalid['trace'] and rows()==before)
            for fields in ({'code':'bad-code'}, {'name':''}, {'name':'   '}, {'code':4}, {'extra':'x'}):
                before=rows(); status,invalid=call('prepare',dict(body,**fields))
                check('invalid prepare '+repr(fields),status==422 and not invalid['trace'] and rows()==before)
            with closing(sqlite3.connect(work/'.lab/relationships.sqlite3')) as db:
                fk=db.execute('PRAGMA foreign_key_list(lab_trade)').fetchall()
                check('foreign key policy is RESTRICT',len(fk)==1 and fk[0][2]=='lab_product' and fk[0][6]=='RESTRICT')
                db.execute('PRAGMA foreign_keys=ON')
                try: db.execute("INSERT INTO lab_trade(trade_no,product_id,quantity) VALUES ('BAD',999,1)")
                except sqlite3.IntegrityError: orphan_blocked=True
                else: orphan_blocked=False
                db.rollback()
                check('orphan trade is blocked by database',orphan_blocked)
                db.execute("CREATE TRIGGER qa_other BEFORE DELETE ON lab_product BEGIN SELECT RAISE(ABORT,'other failure'); END")
                db.commit()
            status, other = call('delete', {'code':'A001'})
            check('unexpected error is not normal deletion rejection',status==500 and other['outcome']=='취소')
            with closing(sqlite3.connect(work/'.lab/relationships.sqlite3')) as db:
                db.execute('DROP TRIGGER qa_other');db.commit()
                db.execute("INSERT INTO lab_product(code,name) VALUES ('FREE','거래 없음')");db.commit()
            status, free = call('delete',{'code':'FREE'})
            check('unreferenced product really deletes',status==200 and not any(p['code']=='FREE' for p in free['snapshot']['products']))
            before=rows();request(port,'/api/reset',{})
            check('exercise 1 reset preserves exercise 2',rows()==before)
            with closing(sqlite3.connect(work/'.lab/stock.sqlite3')) as db:
                db.execute("UPDATE stock SET quantity=6 WHERE product_code='A001'")
                db.execute("INSERT INTO stock_history(product_code,change_qty,reason) VALUES ('A001',6,'입고')")
                db.commit()
            before_stock=database(work)
            status,reset=call('reset',{})
            check('exercise 2 reset clears only relationships',status==200 and not reset['snapshot']['products'] and database(work)==before_stock)
            status,different=call('prepare',{'code':'C900','name':'직접 입력한 이름','quantity':9})
            check('different inputs are not hardcoded',status==200 and different['snapshot']['selection']==[{'code':'C900','name':'직접 입력한 이름'}] and different['snapshot']['trades'][0]['quantity']==9)
            call('reset',{})
            with closing(sqlite3.connect(work/'.lab/relationships.sqlite3')) as db:
                db.execute("CREATE TRIGGER qa_trade BEFORE INSERT ON lab_trade BEGIN SELECT RAISE(ABORT,'injected failure'); END");db.commit()
            status, failed=call('prepare',body)
            check('preparation write failure rolls back both rows',status==500 and rows()==[[],[]] and any(t['sql']=='ROLLBACK' for t in failed['trace']))
            with closing(sqlite3.connect(work/'.lab/relationships.sqlite3')) as db:
                db.execute('DROP TRIGGER qa_trade');db.commit()
            call('prepare',body)
            with closing(sqlite3.connect(work/'.lab/relationships.sqlite3')) as db:
                db.execute('DROP TABLE lab_trade')
                db.execute('''CREATE TABLE lab_trade(id INTEGER PRIMARY KEY,trade_no TEXT UNIQUE,product_id INTEGER REFERENCES lab_product(id) ON DELETE CASCADE,quantity INTEGER)''')
                db.execute("INSERT INTO lab_trade(trade_no,product_id,quantity) SELECT 'T-0001',id,5 FROM lab_product");db.commit()
            before=rows();status,bad=call('delete',{'code':'A001'})
            check('CASCADE misconfiguration fails and rolls back',status==500 and rows()==before and bad['outcome']=='취소')
        print('RESULT Pass='+str(len(passed))+' Fail=0 Not Run=0')
        print('UI and learner tool generation require separate checks. Original data/server were not used.')
        return 0
    except AssertionError as error:
        print('FAIL',str(error));print('RESULT passed-before-failure='+str(len(passed)));return 1
    except Exception as error:
        print('NOT RUN',type(error).__name__,str(error));return 2


if __name__=='__main__':
    raise SystemExit(main())
