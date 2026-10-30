"""제공 관찰 서버. 학습자 함수의 검증·계산을 대신하지 않는다."""
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from uuid import uuid4
import argparse
import json
import sys
import types

ROOT = Path(__file__).resolve().parent


def load_example(root):
    """수정한 소스를 매 요청 새로 읽으며 bytecode 캐시를 사용하지 않는다."""
    path = root / 'order_example.py'
    module = types.ModuleType('_ch08_current_example')
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(path.read_text(encoding='utf-8-sig'), str(path), 'exec'), module.__dict__)
    return module


def observe(data, root=ROOT):
    result = {
        'request_id': str(uuid4()), 'status_code': 200, 'detail': '실행',
        'input': deepcopy(data), 'steps': [], 'item': None, 'amounts': None,
        'calculation_status': '미실행',
    }
    stage = '업무 파일 읽기'
    try:
        module = load_example(Path(root))
        stage = '품목 검증'
        step = {'stage': stage, 'input': deepcopy(data['payload'])}
        result['steps'].append(step)
        item = module.validate_item(data['payload'])
        step['output'] = deepcopy(item)
        result['item'] = deepcopy(item)
        if not isinstance(item, dict) or set(item) != {'prod_code', 'qty'}:
            raise TypeError('검증 반환 필드는 prod_code·qty여야 합니다. 실제 반환값을 확인하세요.')
        stage = '서버 기준 계산'
        result['calculation_status'] = '실행 중'
        step = {'stage': stage, 'input': {
            'item': deepcopy(item), 'server_unit_price': data['server_unit_price'],
            'is_vat': data['is_vat'],
        }}
        result['steps'].append(step)
        amounts = module.calculate_amounts(
            item, server_unit_price=data['server_unit_price'], is_vat=data['is_vat'])
        step['output'] = deepcopy(amounts)
        result['amounts'] = deepcopy(amounts)
        if not isinstance(amounts, dict) or set(amounts) != {
            'unit_price', 'supply_amount', 'vat_amount', 'total_amount'
        }:
            raise TypeError('계산 반환 필드 규약이 다릅니다. 실제 반환값을 확인하세요.')
        result.update(detail='학습자 함수의 실제 반환값입니다.', calculation_status='완료')
    except (FileNotFoundError, NotImplementedError) as error:
        result.update(status_code=501, detail='업무 파일이 없거나 미구현입니다. AI와 구현한 뒤 다시 실행하세요.')
        result['error'] = {'stage': stage, 'type': type(error).__name__, 'message': str(error)}
    except Exception as error:
        result.update(status_code=400 if isinstance(error, ValueError) else 500,
                      detail=f'{stage}: {type(error).__name__}: {error}')
        result['error'] = {'stage': stage, 'type': type(error).__name__, 'message': str(error)}
    if 'error' in result:
        if result['steps']:
            result['steps'][-1]['error'] = result['error']
        if result['calculation_status'] == '실행 중':
            result['calculation_status'] = '실패'
    try:
        json.dumps(result, allow_nan=False)
    except (TypeError, ValueError):
        # 비 JSON 반환값도 정상 금액으로 바꾸지 않고 repr로 남긴다.
        result = json.loads(json.dumps(result, default=repr), parse_constant=lambda value: f'<{value}>')
        result.update(status_code=500, detail='JSON으로 표시할 수 없는 반환값입니다. 실제 반환 형식을 확인하세요.')
        if result['calculation_status'] == '완료':
            result['calculation_status'] = '실패'
    return result


def create_server(port=8308, root=ROOT):
    root = Path(root)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, data):
            raw = json.dumps(data, ensure_ascii=False, allow_nan=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            files = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'),
                     '/style.css': ('style.css', 'text/css')}
            entry = files.get(self.path)
            if not entry:
                self.reply(404, {'detail': '경로를 찾을 수 없습니다.'})
                return
            name, mime = entry
            raw = (root / 'frontend' / name).read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', mime + '; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            if self.path != '/api/calculate':
                self.reply(404, {'detail': '경로를 찾을 수 없습니다.'})
                return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 65536:
                    raise ValueError('요청 크기를 확인하세요.')
                body = self.rfile.read(size)
            except ValueError as error:
                self.reply(422, {'detail': str(error)})
                return
            origin = self.headers.get('Origin')
            if origin and origin != 'http://' + self.headers.get('Host', ''):
                self.reply(403, {'detail': '다른 사이트의 실습 요청은 받지 않습니다.'})
                return
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                self.reply(415, {'detail': 'JSON 요청이 필요합니다.'})
                return
            try:
                data = json.loads(body, parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
                if not isinstance(data, dict) or not {'payload', 'server_unit_price', 'is_vat'} <= set(data):
                    raise ValueError('payload·server_unit_price·is_vat이 필요합니다.')
            except (ValueError, UnicodeError) as error:
                self.reply(422, {'detail': str(error)})
                return
            result = observe(data, root)
            self.reply(result['status_code'], result)

    return HTTPServer(('127.0.0.1', port), Handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8308)
    args = parser.parse_args()
    server = create_server(args.port)
    print(f'Open http://127.0.0.1:{server.server_port} ; stop with Ctrl+C.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
