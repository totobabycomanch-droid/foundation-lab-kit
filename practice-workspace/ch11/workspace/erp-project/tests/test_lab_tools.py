"""전용 대상 보호·SQL 원자 적용·독자 데이터 보존·프로세스 경계 회귀 검사."""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lab
import lab_db as db
import lab_servers as servers

REF = 'abcdefghijklmnopqrst'
URL = f'postgresql://postgres:private-test-password@db.{REF}.supabase.co:5432/postgres'


class DatabaseBoundaryTests(unittest.TestCase):
    def test_direct_target_and_session_pooler(self):
        self.assertEqual(db.validate_target(URL, REF)['sslmode'], 'require')
        pooler = f'postgresql://postgres.{REF}:private-test-password@aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres'
        self.assertEqual(db.validate_target(pooler, REF)['dbname'], 'postgres')

    def test_wrong_project_host_port_database_tls_and_query_are_rejected(self):
        invalid = [URL.replace(REF, 'x' * 20), URL.replace(':5432', ':6543'),
                   URL.replace('/postgres', '/production'), URL + '?sslmode=disable',
                   URL + '?options=-csearch_path%3Dother', URL.replace('.supabase.co', '.supabase.co.attacker.test')]
        for url in invalid:
            with self.subTest(url='redacted'), self.assertRaises(db.LabError):
                db.validate_target(url, REF)

    def test_config_is_local_not_inherited(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'DATABASE_URL': URL}):
            with self.assertRaisesRegex(db.LabError, 'local_settings_required'):
                db.settings(Path(folder))
            (Path(folder) / '.env').write_text(f'DATABASE_URL={URL}\nCH11_PROJECT_REF={REF}\n', encoding='utf-8')
            self.assertEqual(db.settings(Path(folder))['host'], f'db.{REF}.supabase.co')

    def test_init_refuses_existing_work(self):
        cur = Mock()
        with patch.object(db, 'objects', return_value={'orders'}):
            with self.assertRaisesRegex(db.LabError, 'existing_objects_preserved'):
                db.initialize(cur)
        cur.execute.assert_not_called()

    def test_marker_required_before_sql(self):
        cur = Mock()
        cur.fetchone.return_value = (None,)
        with self.assertRaisesRegex(db.LabError, 'marker_missing'):
            db.apply_sql(cur, '10_schema.sql', 'CREATE TABLE x(id int);', 'digest')
        self.assertEqual(cur.execute.call_count, 1)

    def test_apply_identical_digest_skips_execution(self):
        cur = Mock()
        cur.fetchone.side_effect = [('marker',), (1,), ('history',), ('digest',)]
        self.assertEqual(db.apply_sql(cur, '10_schema.sql', 'CREATE TABLE x(id int);', 'digest'), 'already_applied')
        self.assertFalse(any('CREATE TABLE x' in str(call) for call in cur.execute.call_args_list))

    def test_changed_sql_preserves_database(self):
        cur = Mock()
        cur.fetchone.side_effect = [('marker',), (1,), ('history',), ('old-digest',)]
        with self.assertRaisesRegex(db.LabError, 'applied_sql_changed'):
            db.apply_sql(cur, '10_schema.sql', 'CREATE TABLE x(id int);', 'new-digest')

    def test_untracked_business_objects_are_not_adopted(self):
        cur = Mock()
        cur.fetchone.side_effect = [('marker',), (1,), ('history',), None, (0,)]
        with patch.object(db, 'objects', return_value={'orders', 'foundation_lab_marker', 'ch11_sql_history'}):
            with self.assertRaisesRegex(db.LabError, 'untracked_objects_preserved'):
                db.apply_sql(cur, '10_schema.sql', 'CREATE TABLE x(id int);', 'digest')

    def test_sql_path_transaction_and_destructive_commands(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sql').mkdir()
            outside = root / 'outside.sql'
            outside.write_text('CREATE TABLE x(id int);', encoding='utf-8')
            with self.assertRaises(db.LabError):
                db.sql_source('../outside.sql', root)
            for source in ('CREATE TABLE x(id int); COMMIT;', 'DELETE FROM orders;',
                           'ALTER TABLE orders DROP COLUMN status;', '/* nested /* comment */ */ BEGIN;'):
                (root / 'sql/schema.sql').write_text(source, encoding='utf-8')
                with self.subTest(source=source), self.assertRaises(db.LabError):
                    db.sql_source('schema.sql', root)

    def test_function_body_and_comments_do_not_split_top_level_sql(self):
        source = """-- COMMIT;
        CREATE TABLE x(id int, note text DEFAULT 'COMMIT;');
        CREATE OR REPLACE FUNCTION f() RETURNS void AS $body$
        BEGIN INSERT INTO x VALUES(1, 'test'); END;
        $body$ LANGUAGE plpgsql; /* nested /* COMMIT; */ comment */
        """
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sql').mkdir()
            (root / 'sql/schema.sql').write_text(source, encoding='utf-8')
            self.assertEqual(db.sql_source('schema.sql', root)[1], source)

    def test_existing_reader_result_is_preserved(self):
        cur = Mock()
        cur.fetchone.side_effect = [('PROD-100', 3, '정상 승인용 주문 A', 'HQ'), ('정상 확인용 상품', 'HQ'), None]
        with patch.object(db, 'require_schema'):
            self.assertEqual(db.prepare_case(cur, 'A'), 'preserved')
        for call in cur.execute.call_args_list:
            self.assertTrue(call.args[0].startswith('SELECT'))

    def test_standard_and_escape_strings_follow_postgres_rules(self):
        # 일반 문자열의 역슬래시가 뒤따르는 COMMIT을 숨기지 않아야 한다.
        tokens = db.statements("CREATE TABLE x(note text DEFAULT '\\'); COMMIT;")
        self.assertEqual(tokens[-1], ['COMMIT'])
        tokens = db.statements("CREATE TABLE x(note text DEFAULT E'escaped\\\'quote;');")
        self.assertEqual(len(tokens), 1)

    def test_reset_is_scoped_to_requested_order_and_product(self):
        cur = Mock()
        cur.fetchone.side_effect = [('PROD-200', 3, '재고 부족용 주문 B', 'HQ'), ('부족 확인용 상품', 'HQ'), None]
        with patch.object(db, 'require_schema'):
            self.assertEqual(db.prepare_case(cur, 'B', reset=True), 'reset')
        writes = [call for call in cur.execute.call_args_list if not call.args[0].startswith('SELECT')]
        self.assertEqual(len(writes), 3)
        self.assertTrue(all('WHERE' in call.args[0] for call in writes))
        self.assertNotIn('PROD-100', str(writes))
        self.assertIn('quantity=1', writes[-1].args[0])

    def test_edited_reader_quantity_is_preserved(self):
        cur = Mock()
        cur.fetchone.side_effect = [('PROD-100', 8, '정상 승인용 주문 A', 'HQ'), ('정상 확인용 상품', 'HQ'), None]
        with patch.object(db, 'require_schema'):
            self.assertEqual(db.prepare_case(cur, 'A'), 'preserved')
        self.assertTrue(all(call.args[0].startswith('SELECT') for call in cur.execute.call_args_list))

    def test_shared_product_blocks_reset(self):
        cur = Mock()
        cur.fetchone.side_effect = [('PROD-100', 3, '정상 승인용 주문 A', 'HQ'), ('정상 확인용 상품', 'HQ'), (1,)]
        with patch.object(db, 'require_schema'), self.assertRaisesRegex(db.LabError, 'product_shared'):
            db.prepare_case(cur, 'A', reset=True)

    def test_database_context_rolls_back_and_closes_on_failure(self):
        conn = Mock()
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(return_value=False)
        cur = Mock()
        cursor_context = Mock()
        cursor_context.__enter__ = Mock(return_value=cur)
        cursor_context.__exit__ = Mock(return_value=False)
        conn.cursor.return_value = cursor_context
        cur.fetchone.return_value = ('postgres', 'postgres')
        import psycopg2
        with patch.object(db, 'settings', return_value={'user': 'postgres'}), patch.object(psycopg2, 'connect', return_value=conn):
            with self.assertRaisesRegex(ValueError, 'failure'):
                with db.connection():
                    raise ValueError('failure')
        self.assertEqual(conn.__exit__.call_args.args[0], ValueError)
        conn.close.assert_called_once()


class ServerBoundaryTests(unittest.TestCase):
    def test_unowned_port_is_not_reused_or_killed(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(servers, 'occupied', return_value=True):
            root = Path(folder)
            with self.assertRaisesRegex(RuntimeError, 'port_in_use'):
                servers.start('api', root)
            self.assertEqual(servers.stop('api', root), 'not_owned_no_process_stopped')

    def test_stale_process_record_is_not_stopped(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            servers.write_json(servers.runtime(root) / 'api.json', {'state': 'running', 'heartbeat': 0, 'token': 'old'})
            self.assertEqual(servers.stop('api', root), 'not_owned_no_process_stopped')
            self.assertFalse((servers.runtime(root) / 'api.stop').exists())

    def test_sanitized_output_removes_url_password_and_ansi(self):
        line = f'\x1b[31merror {URL} private-test-password\x1b[0m'
        result = servers.redact(line, [URL, 'private-test-password'])
        self.assertNotIn('private-test-password', result)
        self.assertNotIn('postgresql://', result)
        self.assertNotIn('\x1b', result)

    def test_raw_database_errors_are_not_printed(self):
        output = io.StringIO()
        with patch.object(lab, 'run', side_effect=ValueError(URL)), redirect_stdout(output):
            self.assertEqual(lab.main(['inspect']), 1)
        self.assertNotIn(URL, output.getvalue())
        self.assertIn('Not Run', output.getvalue())


if __name__ == '__main__':
    unittest.main()
