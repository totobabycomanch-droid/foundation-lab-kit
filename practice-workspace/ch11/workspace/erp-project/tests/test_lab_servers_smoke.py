"""DB 없는 임시 FastAPI·Vite 프로젝트로 실행·재개·종료를 실제 확인한다."""
import importlib.util
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lab_servers


class ServerSmokeTests(unittest.TestCase):
    def test_api_start_reuse_stop_and_restart(self):
        if lab_servers.occupied(8000):
            self.skipTest('port 8000 already in use; existing process preserved')
        source = Path(lab_servers.__file__)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'erp-project'
            root.mkdir()
            shutil.copyfile(source, root / 'lab_servers.py')
            (root / 'api').mkdir()
            (root / 'api/__init__.py').write_text('', encoding='utf-8')
            (root / 'api/main.py').write_text(
                "from fastapi import FastAPI\napp = FastAPI()\n"
                "print('postgresql://postgres:smoke-secret@localhost/postgres smoke-secret', flush=True)\n",
                encoding='utf-8')
            (root / '.env').write_text('DATABASE_URL=postgresql://postgres:smoke-secret@localhost/postgres\n', encoding='utf-8')
            spec = importlib.util.spec_from_file_location('smoke_servers', root / 'lab_servers.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            try:
                self.assertEqual(module.start('api')['http'], 'Pass')
                token = module.record(root, 'api')['token']
                self.assertEqual(module.start('api')['state'], 'running')
                self.assertEqual(module.record(root, 'api')['token'], token)
                log = (root / '.ch11-runtime/api.log').read_text(encoding='utf-8')
                self.assertNotIn('smoke-secret', log)
                self.assertIn('[redacted]', log)
                self.assertEqual(module.stop('api'), 'stopped')
                self.assertFalse(module.occupied(8000))
                self.assertEqual(module.start('api')['http'], 'Pass')
                self.assertNotEqual(module.record(root, 'api')['token'], token)
            finally:
                module.stop('api')
                # supervisor가 최종 상태 기록과 파일 핸들 해제를 마치도록 한다.
                time.sleep(.5)

    def test_vite_start_and_stop(self):
        if lab_servers.occupied(5173):
            self.skipTest('port 5173 already in use; existing process preserved')
        original = Path(lab_servers.__file__).resolve().parent
        vite = original.parent / 'frontend-project/node_modules/vite/bin/vite.js'
        node = shutil.which('node')
        if not vite.is_file() or not node:
            self.skipTest('installed Vite and Node required')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'erp-project'
            front = root.parent / 'frontend-project'
            root.mkdir()
            front.mkdir()
            (front / 'index.html').write_text('<!doctype html><title>ch11 smoke</title><p>Ready</p>', encoding='utf-8')
            # 실제 Vite 경로는 이 로컬 검사본에서만 지정한다. 사용자 화면 코드는 실행하지 않는다.
            source = Path(lab_servers.__file__).read_text(encoding='utf-8')
            source = source.replace("vite = front / 'node_modules/vite/bin/vite.js'", f'vite = Path({str(vite)!r})')
            (root / 'lab_servers.py').write_text(source, encoding='utf-8')
            spec = importlib.util.spec_from_file_location('smoke_web_servers', root / 'lab_servers.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            try:
                self.assertEqual(module.start('web')['http'], 'Pass')
                self.assertEqual(module.stop('web'), 'stopped')
                self.assertFalse(module.occupied(5173))
            finally:
                module.stop('web')
                time.sleep(.5)


if __name__ == '__main__':
    unittest.main()
