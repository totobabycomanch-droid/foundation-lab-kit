"""Python 표준 라이브러리 로컬 관찰 서버. 업무 트랜잭션을 대신 구현하지 않는다."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from uuid import uuid4
import argparse
import importlib
import json
import os
from lab_store import Store
from lab_contracts import LabError

ROOT=Path(__file__).resolve().parent


def create_server(port=8307, data_root=None):
    store=Store(data_root or ROOT/'.lab')
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,status,data):
            raw=json.dumps(data,ensure_ascii=False).encode('utf-8')
            self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            parsed=urlsplit(self.path)
            files={'/':('frontend/index.html','text/html'),'/frontend/app.js':('frontend/app.js','text/javascript'),'/frontend/style.css':('frontend/style.css','text/css')}
            if parsed.path in files:
                name,mime=files[parsed.path];raw=(ROOT/name).read_bytes()
                self.send_response(200);self.send_header('Content-Type',mime+'; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
            elif parsed.path=='/api/state':
                self.dispatch('state',{'session':parse_qs(parsed.query).get('session',[''])[0]})
            else:self.reply(404,{'detail':'경로를 찾을 수 없습니다.'})
        def do_POST(self):
            try:
                origin=self.headers.get('Origin')
                if origin and origin!='http://'+self.headers.get('Host',''):raise LabError(403,'다른 사이트의 실습 요청은 받지 않습니다.')
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=65536:raise LabError(422,'요청 크기를 확인하세요.')
                if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise LabError(415,'JSON 요청이 필요합니다.')
                data=json.loads(self.rfile.read(size))
                if not isinstance(data,dict):raise ValueError()
            except LabError as error:self.reply(error.status,{'status_code':error.status,'request_id':str(uuid4()),'detail':error.detail,'trace':[],'snapshot':None});return
            except (ValueError,TypeError):self.reply(422,{'status_code':422,'request_id':str(uuid4()),'detail':'입력 형식을 확인하세요.','trace':[],'snapshot':None});return
            self.dispatch(urlsplit(self.path).path.removeprefix('/api/'),data)
        def dispatch(self,action,data):
            trace=[];result={'request_id':str(uuid4()),'status_code':200,'detail':'DB에서 다시 조회했습니다.','outcome':'조회','trace':trace,'snapshot':None}
            try:
                session=data.get('session')
                if action=='session':
                    session,result['snapshot']=store.new_session(trace);result['session']=session
                elif action=='state':result['snapshot']=store.observe(session,trace)
                elif action=='reset':result['snapshot']=store.reset_sale(session,data.get('initial'),trace);result.update(detail='판매 사례만 초기화했습니다.',outcome='준비')
                elif action=='failure':result['snapshot']=store.failure(session,data.get('enabled'),trace);result.update(detail='실습용 저장 실패 장치를 변경했습니다.',outcome='설정')
                elif action=='compare':
                    run=importlib.reload(importlib.import_module('transaction_example')).run_transaction
                    cases=store.compare(session,data.get('initial'),data.get('quantity'),run)
                    result['cases']=cases;result['status_code']=max(c['status_code'] for c in cases)
                    result.update(detail='두 독립 DB의 실제 결과를 확인하세요.',outcome='비교')
                elif action=='sale':
                    sell=importlib.reload(importlib.import_module('sale_example')).sell
                    status,detail,outcome,number,s=store.sale(session,data.get('key'),data.get('product'),data.get('quantity'),sell,trace)
                    result.update(status_code=status,detail=detail,outcome=outcome,sale_no=number,snapshot=s)
                else:raise LabError(404,'경로를 찾을 수 없습니다.')
            except LabError as error:result.update(status_code=error.status,detail=error.detail,outcome='미실행')
            except Exception as error:result.update(status_code=500,detail='실행 파일과 터미널 오류를 확인하세요: '+type(error).__name__,outcome='미확인')
            self.reply(result['status_code'],result)
    return HTTPServer(('127.0.0.1',port),Handler)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8307);parser.add_argument('--data-root')
    parser.add_argument('--port-file',help=argparse.SUPPRESS);args=parser.parse_args()
    server=create_server(args.port,args.data_root)
    if args.port_file:Path(args.port_file).write_text(str(server.server_port))
    print('Open http://127.0.0.1:'+str(server.server_port)+' ; stop with Ctrl+C.',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
