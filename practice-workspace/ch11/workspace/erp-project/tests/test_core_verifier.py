"""검사기가 실패·미실행·정리 실패를 통과로 바꾸지 않는지 확인한다."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lab_db as db
import verify_core as core


def readers():
    return [({'order_id': value[0], 'product_id': value[1], 'order_name': value[2],
              'quantity': 3, 'status': 'CREATED'},
             {'product_name': value[3], 'quantity': value[4]}, []) for value in db.CASES.values()]


@contextlib.contextmanager
def fake_connection():
    yield Mock()


class CoreVerifierTests(unittest.TestCase):
    def test_not_run_exits_nonzero_and_skips_dependent_http(self):
        def unavailable(report):
            for name in core.DB_CHECKS:
                core.add(report, name, 'Not Run', 'database_not_ready')
        output = io.StringIO()
        with patch.object(core, 'run_database', unavailable), patch.object(core, 'run_http') as http, \
                patch.object(core, 'run_build', lambda report: core.add(report, 'build', 'Pass')), \
                contextlib.redirect_stdout(output):
            self.assertEqual(core.main([]), 1)
        http.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())['http.normal']['result'], 'Not Run')

    def test_optional_checks_do_not_hide_successful_selected_checks(self):
        with patch.object(core, 'run_build', lambda report: core.add(report, 'build', 'Pass')), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(core.main(['--only', 'build']), 0)

    def test_optimized_python_cannot_report_unexecuted_assertions_as_pass(self):
        with patch.object(core.sys, 'flags', SimpleNamespace(optimize=1)), \
                patch.object(core, 'run_database') as database, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(core.main([]), 1)
        database.assert_not_called()

    def test_missing_database_never_starts_an_api(self):
        @contextlib.contextmanager
        def unavailable():
            raise db.LabError('local_settings_required')
            yield
        report = {}
        with patch.object(db, 'connection', unavailable), patch.object(core.servers, 'start') as start:
            core.run_http(report)
        start.assert_not_called()
        self.assertTrue(all(row['result'] == 'Not Run' for row in report.values()))

    def test_cleanup_conflict_preserves_existing_data(self):
        cur = Mock()
        cur.fetchone.return_value = ('OTHER-PRODUCT', 'personal order', 'OTHER')
        with self.assertRaises(AssertionError):
            core.cleanup(cur, [core.fixture(10, 'test')])
        self.assertTrue(all(call.args[0].startswith('SELECT') for call in cur.execute.call_args_list))

    def run_http_double(self, request, stored):
        report = {}
        with patch.object(db, 'connection', fake_connection), patch.object(db, 'require_schema'), \
                patch.object(core, 'reader_snapshot', return_value=readers()), \
                patch.object(core.servers, 'start'), patch.object(core, 'seed'), \
                patch.object(core, 'request', side_effect=request), patch.object(core, 'current', side_effect=stored), \
                patch.object(core, 'cleanup') as cleanup, patch.object(core, 'no_fixture_rows'):
            core.run_http(report)
            cleaned = cleanup.call_args.args[1]
        self.assertEqual(len(cleaned), 2)
        self.assertTrue(all(item['product'].startswith('CH11-TEST-') for item in cleaned))
        self.assertFalse({value[0] for value in db.CASES.values()} & {item['id'] for item in cleaned})
        return report

    def query_response(self):
        return {'items': [dict(order_id=o['order_id'], order_name=o['order_name'], product_id=o['product_id'],
                               product_name=s['product_name'], qty=3, current_stock=s['quantity'], status='CREATED')
                          for o, s, _ in readers()]}

    def test_http_200_without_database_change_fails(self):
        responses = iter([(200, self.query_response()), (200, {'status': 'success'}),
                          (400, {'detail': 'shortage'}), (400, {'detail': 'already approved'})])
        states = iter([('CREATED', 10, 0, None), ('CREATED', 2, 0, None), ('CREATED', 10, 0, None)])
        report = self.run_http_double(lambda *args: next(responses), lambda *args: next(states))
        self.assertEqual(report['http.normal']['result'], 'Fail')
        self.assertEqual(report['http.test_rows_removed']['result'], 'Pass')

    def test_matching_http_and_database_results_pass(self):
        responses = iter([(200, self.query_response()), (200, {'status': 'success'}),
                          (400, {'detail': 'shortage'}), (400, {'detail': 'already approved'})])
        states = iter([('PAID', 7, 1, -3), ('CREATED', 2, 0, None), ('PAID', 7, 1, -3)])
        report = self.run_http_double(lambda *args: next(responses), lambda *args: next(states))
        self.assertEqual(set(report), set(core.HTTP_CHECKS))
        self.assertTrue(all(value['result'] == 'Pass' for value in report.values()))

    def test_http_failures_still_run_fixture_cleanup(self):
        def failing(method, *args):
            if method == 'GET':
                return 200, self.query_response()
            raise TimeoutError()
        report = self.run_http_double(failing, lambda *args: None)
        self.assertEqual(report['http.normal']['result'], 'Fail')
        self.assertEqual(report['http.test_rows_removed']['result'], 'Pass')

    def test_remaining_ledger_is_detected(self):
        cur = Mock()
        cur.fetchone.side_effect = [None, None, (1,)]
        with self.assertRaises(AssertionError):
            core.no_fixture_rows(cur, [core.fixture(10, 'test')])

    def test_build_failure_and_log_redaction(self):
        with tempfile.TemporaryDirectory() as folder:
            backend = Path(folder) / 'backend'
            backend.mkdir()
            vite = Path(folder) / 'frontend-project/node_modules/vite/bin/vite.js'
            vite.parent.mkdir(parents=True)
            vite.write_text('', encoding='utf-8')
            result = SimpleNamespace(returncode=1, stdout='postgresql://test:secret@host/db secret', stderr='')
            report = {}
            with patch.object(db, 'ROOT', backend), patch.object(db, 'settings', return_value={'password': 'secret'}), \
                    patch.object(core.shutil, 'which', return_value='npm'), patch.object(core.subprocess, 'run', return_value=result):
                core.run_build(report)
            self.assertEqual(report['build']['result'], 'Fail')
            self.assertNotIn('secret', (backend / '.ch11-runtime/build.log').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
