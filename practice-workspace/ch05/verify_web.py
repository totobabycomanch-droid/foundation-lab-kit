"""Exercise the current web code in a disposable copy with a private DB/server."""
from pathlib import Path
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError
from contextlib import contextmanager, closing
import json
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent


def worker(workspace):
    sys.path.insert(0, str(workspace))
    import uvicorn
    from backend.app import app
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0)); listener.listen(128)
        (workspace/'port.json').write_text(json.dumps(listener.getsockname()[1]))
        uvicorn.Server(uvicorn.Config(app, log_level='error', access_log=False)).run(sockets=[listener])


@contextmanager
def isolated():
    with tempfile.TemporaryDirectory(prefix='ch05-web-check-') as d:
        workspace = Path(d)
        for name in ('backend', 'frontend'):
            shutil.copytree(ROOT/name, workspace/name, ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        with tempfile.TemporaryFile() as logs:
            process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), '--worker', str(workspace)],
                cwd=workspace, stdin=subprocess.DEVNULL, stdout=logs, stderr=logs,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:
                for _ in range(200):
                    if process.poll() is not None:
                        raise RuntimeError('Temporary server exited; check Python dependencies and imports')
                    try:
                        port=json.loads((workspace/'port.json').read_text())
                        request(port, '/api/state')
                        break
                    except (OSError, ValueError):
                        time.sleep(.05)
                else:
                    raise RuntimeError('Temporary server startup timeout')
                yield workspace, port
            finally:
                if process.poll() is None:
                    process.terminate()
                    try: process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill(); process.wait(timeout=5)


def request(port, path, body=None):
    payload = json.dumps(body).encode() if body is not None else None
    req=Request(f'http://127.0.0.1:{port}'+path, data=payload,
        headers={'Content-Type':'application/json'} if payload else {})
    try: response=build_opener(ProxyHandler({})).open(req, timeout=5)
    except HTTPError as error: response=error
    with response:
        status, data=response.status, json.loads(response.read())
    assert data['status_code']==status
    assert data['request_id']
    assert [x['step'] for x in data['trace']]==list(range(1,len(data['trace'])+1))
    return status,data


def database(workspace):
    with closing(sqlite3.connect(workspace/'.lab/stock.sqlite3')) as db:
        return {t:db.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall()
                for t in ('products','stock','stock_history')}


def main():
    passed=[]
    def check(label, condition):
        assert condition,label
        passed.append(label);print('PASS',label,flush=True)
    try:
        with isolated() as (workspace,port):
            def move(q, direction='IN', code='A001'):
                return request(port,'/api/movements',{'product_code':code,'direction':direction,'quantity':q})
            def state(code='A001'):
                return request(port,'/api/state?product_code='+code)[1]['snapshot']
            request(port,'/api/reset',{})
            check('starts at zero', state()['current']['quantity']==0 and not state()['history'])
            status, first=move(10)
            check('inbound adds 10 and one history',status==200 and first['snapshot']['current']['quantity']==10
                  and [r['change_qty'] for r in first['snapshot']['history']]==[10])
            status, second=move(3,'OUT')
            check('outbound becomes 7 with history +10/-3',status==200 and second['snapshot']['current']['quantity']==7
                  and [(r['change_qty'],r['reason']) for r in second['snapshot']['history']]==[(10,'입고'),(-3,'출고')]
                  and second['snapshot']['history_quantity']==7)
            check('request IDs are distinct',first['request_id']!=second['request_id'])
            write_trace=[r for r in second['trace'] if r['phase']=='입출고 처리']
            check('actual engine SQL and bindings observed',any(r['parameters'] and r['executed_sql'] for r in write_trace)
                  and any('UPDATE' in s.upper() for r in write_trace for s in r['executed_sql'])
                  and any('INSERT' in s.upper() for r in write_trace for s in r['executed_sql']))
            check('committed then independently reread',second['outcome']=='확정'
                  and any(r['sql']=='COMMIT' for r in write_trace)
                  and any(r['phase']=='저장 후 재조회' and r['rows'] for r in second['trace']))
            before=database(workspace)
            status, denied=move(8,'OUT')
            check('insufficient stock rejects without writes',status==409 and denied['outcome']=='취소'
                  and database(workspace)==before
                  and not any(r['sql'].lstrip().upper().startswith(('UPDATE','INSERT')) for r in denied['trace']))
            for value in (0,-1,1.5,'3',True,None,1000001):
                before=database(workspace);status,result=move(value)
                check('invalid quantity '+repr(value),status==422 and result['outcome']=='미실행'
                      and not result['trace'] and database(workspace)==before)
            for field,value in [('product_code','MISSING'),('direction','OTHER')]:
                body={'product_code':'A001','direction':'IN','quantity':1};body[field]=value
                before=database(workspace);status,_=request(port,'/api/movements',body)
                check('invalid '+field,status==422 and database(workspace)==before)
            move(4,code='B001')
            check('products are independent',state('B001')['current']['quantity']==4 and state()['current']['quantity']==7)
            move(2)
            check('different quantity adds another real movement',state()['current']['quantity']==9
                  and state()['history_quantity']==9 and len(state()['history'])==3)
            with closing(sqlite3.connect(workspace/'.lab/stock.sqlite3')) as db:
                db.execute("CREATE TRIGGER qa_fail_history BEFORE INSERT ON stock_history BEGIN SELECT RAISE(ABORT, 'qa injected write failure'); END;")
                db.commit()
            before=database(workspace);status,failed=move(1)
            check('history write failure rolls back stock and history',status==500 and failed['outcome']=='취소'
                  and database(workspace)==before and failed['snapshot']['current']['quantity']==9)
            failed_write=[r for r in failed['trace'] if r['phase']=='입출고 처리']
            check('rollback visible, failed write not shown as commit',any(r['error'] for r in failed_write)
                  and any(r['sql']=='ROLLBACK' for r in failed_write)
                  and not any(r['sql']=='COMMIT' for r in failed_write))
            with closing(sqlite3.connect(workspace/'.lab/stock.sqlite3')) as db:
                db.execute('DROP TRIGGER qa_fail_history');db.commit()
            reset=request(port,'/api/reset',{})[1]
            check('reset affects only local exercise and clears history',reset['snapshot']['current']['quantity']==0
                  and not reset['snapshot']['history'] and state('B001')['current']['quantity']==0)
        print('RESULT Pass='+str(len(passed))+' Fail=0 Not Run=0')
        print('UI and learner tool generation require separate checks. Original data/server were not used.')
        return 0
    except AssertionError as error:
        print('FAIL',str(error)); print('RESULT passed-before-failure='+str(len(passed)));return 1
    except Exception as error:
        print('NOT RUN',type(error).__name__,str(error));return 2


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--worker':worker(Path(sys.argv[2]))
    else:raise SystemExit(main())
