"""제공 연결 기능 검사. 임시 대역으로 전달·중단·HTTP를 확인하며 업무 검사는 별도다."""
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import json
import unittest

from web_server import create_server, observe

STUB = '''
def validate_item(payload):
    return {'prod_code': payload['prod_code'], 'qty': payload['qty']}
def calculate_amounts(item, *, server_unit_price, is_vat):
    return {'unit_price': server_unit_price, 'supply_amount': item['qty'],
            'vat_amount': is_vat, 'total_amount': 777}
'''


class WebConnectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(prefix='ch08-connection-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'order_example.py'
        self.path.write_text(STUB, encoding='utf-8')
        self.data = {'payload': {'prod_code': '  A001  ', 'qty': 1.5, 'unit_price': 1},
                     'server_unit_price': 105, 'is_vat': '2'}

    def run_code(self, code):
        self.path.write_text(code, encoding='utf-8')
        return observe(self.data, self.root)

    def test_actual_values_and_arguments_are_not_recalculated(self):
        result = observe(self.data, self.root)
        self.assertEqual(result['status_code'], 200)
        self.assertEqual(result['item'], {'prod_code': '  A001  ', 'qty': 1.5})
        self.assertEqual(result['amounts'], {
            'unit_price': 105, 'supply_amount': 1.5, 'vat_amount': '2', 'total_amount': 777})
        self.assertEqual(result['steps'][1]['input']['item'], result['item'])
        self.assertEqual(result['input']['payload']['unit_price'], 1)

    def test_validation_error_prevents_calculation(self):
        result = self.run_code('''
def validate_item(payload): raise ValueError('수량 거부')
def calculate_amounts(*args, **kwargs): raise AssertionError('호출되면 안 됨')
''')
        self.assertEqual(result['status_code'], 400)
        self.assertEqual(result['calculation_status'], '미실행')
        self.assertIsNone(result['amounts'])
        self.assertEqual(len(result['steps']), 1)
        self.assertEqual(result['error']['type'], 'ValueError')

    def test_extra_fields_are_observed_not_silently_removed(self):
        result = self.run_code(STUB.replace("return {'prod_code': payload['prod_code'], 'qty': payload['qty']}", 'return payload'))
        self.assertEqual(result['status_code'], 500)
        self.assertEqual(result['item'], self.data['payload'])
        self.assertEqual(result['calculation_status'], '미실행')

    def test_input_types_are_forwarded_without_coercion(self):
        for qty in (True, False, '5', None, 0, -1, 1.5):
            with self.subTest(qty=qty):
                self.data['payload']['qty'] = qty
                result = observe(self.data, self.root)
                self.assertEqual(type(result['item']['qty']), type(qty))
                self.assertEqual(result['item']['qty'], qty)

    def test_calculation_error_and_recovery_do_not_reuse_old_values(self):
        observe(self.data, self.root)
        result = self.run_code(STUB.replace("return {'unit_price': server_unit_price", "raise ValueError('서버 기준값 오류')\n    return {'unit_price': server_unit_price"))
        self.assertEqual(result['status_code'], 400)
        self.assertEqual(result['calculation_status'], '실패')
        self.assertIsNone(result['amounts'])
        result = self.run_code(STUB)
        self.assertEqual(result['calculation_status'], '완료')

    def test_source_changes_are_loaded_without_cache(self):
        first = observe(self.data, self.root)
        second = self.run_code(STUB.replace('777', '888'))
        self.assertEqual(first['amounts']['total_amount'], 777)
        self.assertEqual(second['amounts']['total_amount'], 888)
        self.assertNotEqual(first['request_id'], second['request_id'])

    def test_missing_unimplemented_and_broken_source(self):
        self.path.unlink()
        self.assertEqual(observe(self.data, self.root)['status_code'], 501)
        self.assertEqual(self.run_code('raise NotImplementedError()')['status_code'], 501)
        self.assertEqual(self.run_code('def broken(')['status_code'], 500)

    def test_non_json_result_is_an_error_not_a_success(self):
        for value in ("float('nan')", 'object()'):
            result = self.run_code(STUB.replace('777', value))
            self.assertEqual(result['status_code'], 500)
            json.dumps(result, allow_nan=False)

    @contextmanager
    def running_server(self):
        # 정적 파일도 실제 HTTP로 확인한다.
        frontend = self.root / 'frontend'
        frontend.mkdir()
        for name in ('index.html', 'app.js', 'style.css'):
            (frontend / name).write_bytes((Path(__file__).parent / 'frontend' / name).read_bytes())
        server = create_server(0, self.root)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f'http://127.0.0.1:{server.server_port}'
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_http_static_files_and_actual_function_call(self):
        with self.running_server() as url:
            for path in ('/', '/app.js', '/style.css'):
                with urlopen(url + path, timeout=5) as response:
                    self.assertEqual(response.status, 200)
            request = Request(url + '/api/calculate', json.dumps(self.data).encode(), {'Content-Type': 'application/json'})
            with urlopen(request, timeout=5) as response:
                self.assertEqual(json.load(response)['amounts']['total_amount'], 777)

    def test_http_invalid_envelopes_and_origin(self):
        with self.running_server() as url:
            for body, headers, status in (
                (b'{}', {'Content-Type': 'application/json'}, 422),
                (b'{broken', {'Content-Type': 'application/json'}, 422),
                (b'{}', {'Content-Type': 'text/plain'}, 415),
                (b'{}', {'Content-Type': 'application/json', 'Origin': 'http://other.invalid'}, 403),
            ):
                with self.subTest(status=status):
                    with self.assertRaises(HTTPError) as error:
                        urlopen(Request(url + '/api/calculate', body, headers), timeout=5)
                    self.assertEqual(error.exception.code, status)


if __name__ == '__main__':
    unittest.main(verbosity=2)
