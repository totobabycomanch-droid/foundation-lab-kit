"""현재 업무 코드를 임시 사본·로컬 서버·별도 DB에서 독립 검사한다."""
from contextlib import contextmanager, closing
from pathlib import Path
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError
import argparse
import importlib
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parent


def request(port, action, body):
    req=Request('http://127.0.0.1:'+str(port)+'/api/'+action,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    try:r=build_opener(ProxyHandler({})).open(req,timeout=8)
    except HTTPError as error:r=error
    with r:status,data=r.status,json.load(r)
    assert data['status_code']==status
    assert data['request_id']
    return status,data


@contextmanager
def isolated():
    with tempfile.TemporaryDirectory(prefix='ch07-web-check-') as folder:
        work=Path(folder)
        for p in ROOT.glob('*.py'):shutil.copy2(p,work/p.name)
        shutil.copytree(ROOT/'frontend',work/'frontend')
        with tempfile.TemporaryFile() as log:
            process=subprocess.Popen([sys.executable,'-B',str(work/'web_server.py'),'--port','0','--data-root',str(work/'data'),'--port-file',str(work/'port.txt')],cwd=work,stdin=subprocess.DEVNULL,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:
                for _ in range(200):
                    if process.poll() is not None:raise RuntimeError('Temporary server exited')
                    try:
                        port=int((work/'port.txt').read_text());request(port,'session',{})
                        break
                    except (OSError,ValueError):time.sleep(.05)
                else:raise RuntimeError('Temporary server startup timeout')
                yield work,port
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:process.wait(timeout=10)
                    except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)


def main(exercise='all'):
    passed=[]
    def check(label,condition):
        assert condition,label
        passed.append(label);print('PASS',label,flush=True)
    try:
        with isolated() as (work,port):
            _,fresh=request(port,'session',{});session=fresh['session']
            def call(action,**kw):return request(port,action,dict(session=session,**kw))
            def state():
                status,r=call('state');assert status==200;return r['snapshot']
            def stock(s,code='A001'):return next(p['qty'] for p in s['stock'] if p['prod_code']==code)
            def sale(key='k1',product='A001',quantity=2):return call('sale',key=key,product=product,quantity=quantity)
            if exercise in ('transaction','all'):
                status,c=call('compare',initial=10,quantity=1)
                check('both comparisons execute real failures',status==200 and all(x['storage_error']=='IntegrityError' for x in c['cases']))
                early,safe=c['cases']
                check('early commit leaves stock 9 and no order',early['snapshot']['stock'][0]['qty']==9 and early['snapshot']['orders_count']==0)
                check('rollback restores stock 10 and no order',safe['snapshot']['stock'][0]['qty']==10 and safe['snapshot']['orders_count']==0)
                check('learner closes both transactions',all(not x['unfinished'] for x in c['cases']) and not any('미완료' in t['phase'] for x in c['cases'] for t in x['trace']))
                for case in c['cases']:
                    check('failed INSERT observed '+case['label'],any(t['error']=='IntegrityError' and t['sql'].lstrip().upper().startswith('INSERT INTO ORDERS') and t['executed_sql'] for t in case['trace']))
                check('early COMMIT precedes failing insert',any(t['sql']=='COMMIT' and '업무 처리' in t['phase'] for t in early['trace']))
                check('safe path has ROLLBACK and no business commit',any(t['sql']=='ROLLBACK' and '업무 처리' in t['phase'] for t in safe['trace']) and not any(t['sql']=='COMMIT' and '업무 처리' in t['phase'] for t in safe['trace']))
                check('comparison leaves sale database unchanged',stock(state())==5 and not state()['sales'])
                status,d=call('compare',initial=12,quantity=2)
                check('different comparison inputs are real',status==200 and [x['snapshot']['stock'][0]['qty'] for x in d['cases']]==[10,12])
                status,_=call('compare',initial=1,quantity=2)
                check('invalid comparison quantity rejected',status==422)
            if exercise in ('sale','all'):
                call('reset',initial=5)
                check('sale starts with stock 5 and no rows',stock(state())==5 and not state()['sales'])
                status,first=sale();s=first['snapshot'];number=first.get('sale_no')
                check('normal sale records stock and sale number',status==200 and type(number) is int and stock(s)==3 and s['sales']==[{'id':number,'request_key':'k1','prod_code':'A001','qty':2}])
                status,retry=sale()
                check('same key returns same number and whole state',status==200 and retry['sale_no']==number and retry['snapshot']==s)
                write=[t for t in retry['trace'] if t['phase']=='판매 업무 처리']
                check('retry executes no additional writes',not any(t['sql'].lstrip().upper().startswith(('UPDATE','INSERT','DELETE','REPLACE')) for t in write))
                check('separate HTTP observations have distinct IDs',first['request_id']!=retry['request_id'])
                for product,qty in (('A001',3),('B001',2)):
                    status,conflict=sale(product=product,quantity=qty)
                    check('same-key changed content rejected '+product,status==409 and conflict['snapshot']==s)
                status,second=sale('k2');s2=second['snapshot']
                check('new key creates separate sale and stock 1',status==200 and second['sale_no']!=number and stock(s2)==1 and len(s2['sales'])==2)
                for q in (0,-1,1.5,'2',True,None,1000001):
                    status,invalid=sale('bad',quantity=q)
                    check('invalid HTTP quantity '+repr(q),status==422 and not invalid['trace'] and state()==s2)
                status,_=sale('missing',product='MISSING')
                check('invalid product preserves whole state',status==422 and state()==s2)
                call('reset',initial=5);status,denied=sale('too-much',quantity=6)
                check('insufficient stock writes nothing',status==409 and stock(denied['snapshot'])==5 and not denied['snapshot']['sales'])
                status,exact=sale('all',quantity=5)
                check('exact stock sale reaches zero',status==200 and stock(exact['snapshot'])==0 and len(exact['snapshot']['sales'])==1)
                call('reset',initial=5);call('failure',enabled=True)
                status,failed=sale('after-failure');sf=failed['snapshot']
                check('real INSERT failure cancels stock and request key',status==500 and failed['outcome']=='취소' and stock(sf)==5 and not sf['sales'])
                check('rollback belongs to learner transaction',any(t['sql']=='ROLLBACK' and t['phase']=='판매 업무 처리' for t in failed['trace']) and not any('미완료' in t['phase'] for t in failed['trace']))
                call('failure',enabled=False);status,recovered=sale('after-failure')
                check('same DB and failed key can retry successfully',status==200 and stock(recovered['snapshot'])==3 and len(recovered['snapshot']['sales'])==1)
                check('engine SQL bindings and fresh read observed',any(t['parameters'] and t['executed_sql'] for t in recovered['trace']) and any('새 연결' in t['phase'] and t['rows'] for t in recovered['trace']))
                _,other=request(port,'session',{})
                check('new session does not reset first session',stock(other['snapshot'])==5 and stock(state())==3)
                status,bad=call('state');check('state reread keeps sales unchanged',status==200 and bad['snapshot']==recovered['snapshot'])
                dbpath=work/'data'/session/'sale.sqlite3'
                with closing(sqlite3.connect(dbpath)) as db:
                    try:
                        db.execute("INSERT INTO sales(request_key,prod_code,qty) VALUES ('after-failure','A001',1)")
                    except sqlite3.IntegrityError:blocked=True
                    else:blocked=False
                    db.rollback()
                check('database independently rejects duplicate keys',blocked)
                call('reset',initial=11);status,different=sale('different',quantity=4)
                check('different sale input is not hardcoded',status==200 and stock(different['snapshot'])==7 and different['snapshot']['sales'][0]['qty']==4)
                _,reset=call('reset',initial=5)
                check('reset clears sales and failure device',stock(reset['snapshot'])==5 and not reset['snapshot']['sales'] and not reset['snapshot']['failure_enabled'])
                # Direct calls ensure learner validation exists beyond provided HTTP validation.
                sys.path.insert(0,str(work))
                try:
                    module=importlib.import_module('sale_example');contracts=importlib.import_module('lab_contracts');store=importlib.import_module('lab_store')
                    for q in (0,-1,1.5,'2',True,None):
                        db=store.TraceDB(dbpath,[],'direct validation')
                        try:
                            try:module.sell(db,'direct','A001',q)
                            except contracts.LabError as e:rejected=e.status==422
                            else:rejected=False
                            check('learner rejects invalid quantity '+repr(q),rejected and not db.in_transaction)
                        finally:db.close()
                finally:sys.path.pop(0)
        print('RESULT Pass='+str(len(passed))+' Fail=0 Not Run=0')
        print('UI and learner AI generation require separate checks. Original data/server were not used.')
        return 0
    except AssertionError as error:
        print('FAIL',str(error));print('RESULT passed-before-failure='+str(len(passed)));return 1
    except Exception as error:
        print('NOT RUN',type(error).__name__,str(error));return 2


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--exercise',choices=['transaction','sale','all'],default='all');a=p.parse_args();raise SystemExit(main(a.exercise))
