"""프로세스 소유권을 유지하는 로컬 서버 실행기. PID만 보고 종료하지 않는다."""
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import uuid
from collections import deque
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parent
PORTS = {'api': 8000, 'web': 5173}
SUPERVISORS = {}


def runtime(root):
    path = root / '.ch11-runtime'
    path.mkdir(exist_ok=True)
    return path


def write_json(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data), encoding='utf-8')
    temp.replace(path)


def record(root, name):
    try:
        return json.loads((runtime(root) / f'{name}.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def occupied(port):
    with socket.socket() as sock:
        sock.settimeout(.2)
        return sock.connect_ex(('127.0.0.1', port)) == 0


def responds(name):
    path = '/openapi.json' if name == 'api' else '/'
    try:
        with build_opener(ProxyHandler({})).open(f'http://127.0.0.1:{PORTS[name]}{path}', timeout=1) as response:
            return response.status == 200
    except Exception:
        return False


def status(root=ROOT):
    result = {}
    for name in PORTS:
        info = record(root, name)
        owned = info.get('state') == 'running' and time.time() - info.get('heartbeat', 0) < 5
        result[name] = {'state': 'running' if owned else 'port_in_use' if occupied(PORTS[name]) else 'stopped',
                        'http': 'Pass' if owned and responds(name) else 'Not Run'}
    return result


def command(root, name):
    if name == 'api':
        if not (root / 'api/main.py').is_file():
            raise RuntimeError('api_implementation_missing')
        return [sys.executable, '-m', 'uvicorn', 'api.main:app', '--host', '127.0.0.1', '--port', '8000'], root
    front = root.parent / 'frontend-project'
    vite = front / 'node_modules/vite/bin/vite.js'
    node = shutil.which('node')
    if not vite.is_file() or not node:
        raise RuntimeError('frontend_dependencies_missing')
    # Volta 등 런처가 별도 Node를 남기지 않게 실제 실행 파일을 선택한다.
    resolved = subprocess.run([node, '-p', 'process.execPath'], capture_output=True, text=True, timeout=5)
    node = resolved.stdout.strip()
    if resolved.returncode != 0 or not Path(node).is_file():
        raise RuntimeError('frontend_dependencies_missing')
    return [node, str(vite), str(front), '--host', '127.0.0.1', '--port', '5173', '--strictPort'], front


def redact(line, secrets):
    line = re.sub(r'\x1b\[[0-9;]*m', '', line)
    for secret in sorted(set(secrets), key=len, reverse=True):
        if secret:
            line = line.replace(secret, '[redacted]')
    return re.sub(r'postgres(?:ql)?(?:\+psycopg2)?://[^\s\x1b]+', '[redacted-db-url]', line)


def supervise(root, name, token):
    from dotenv import dotenv_values
    from urllib.parse import unquote, urlsplit
    values = dotenv_values(root / '.env', interpolate=False)
    url = values.get('DATABASE_URL', '') or ''
    secrets = [url]
    try:
        secrets.append(unquote(urlsplit(url).password or ''))
    except ValueError:
        pass
    path = runtime(root)
    log = path / f'{name}.log'
    lines = deque(maxlen=200)
    child = None
    try:
        args, cwd = command(root, name)
        env = os.environ.copy()
        # 백엔드는 선택한 로컬 설정만 사용한다. 부모 셸의 다른 DB 설정을 넘기지 않는다.
        env.pop('DATABASE_URL', None)
        if name == 'api':
            env['DATABASE_URL'] = url
        env['PYTHONUNBUFFERED'] = '1'
        child = subprocess.Popen(args, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))

        def consume():
            for line in child.stdout:
                lines.append(redact(line, secrets))
                log.write_text(''.join(lines), encoding='utf-8')

        reader = threading.Thread(target=consume, daemon=True)
        reader.start()
        while child.poll() is None:
            write_json(path / f'{name}.json', {'state': 'running', 'token': token, 'heartbeat': time.time()})
            stop = path / f'{name}.stop'
            if stop.is_file() and stop.read_text(encoding='utf-8') == token:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)
                break
            time.sleep(.2)
        reader.join(timeout=2)
    except Exception:
        # 실행 전 오류에서도 연결값을 포함할 수 있는 예외 전문을 쓰지 않는다.
        log.write_text('server_supervisor_failed\n', encoding='utf-8')
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            child.wait(timeout=5)
        write_json(path / f'{name}.json', {'state': 'stopped', 'token': token, 'heartbeat': time.time()})


def start(name, root=ROOT):
    current = status(root)[name]
    if current['state'] == 'running':
        if current['http'] != 'Pass':
            raise RuntimeError(f'{name}_startup_failed_check_sanitized_logs')
        return current
    if occupied(PORTS[name]):
        raise RuntimeError(f'{name}_port_in_use_no_process_stopped')
    command(root, name)
    token = uuid.uuid4().hex
    SUPERVISORS[token] = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), '--serve', name, token], cwd=root,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        info = record(root, name)
        if info.get('token') == token:
            if info.get('state') == 'stopped':
                break
            if responds(name):
                return status(root)[name]
        time.sleep(.2)
    stop(name, root)
    raise RuntimeError(f'{name}_startup_failed_check_sanitized_logs')


def stop(name, root=ROOT):
    info = record(root, name)
    if info.get('state') != 'running' or time.time() - info.get('heartbeat', 0) >= 5:
        return 'not_owned_no_process_stopped'
    (runtime(root) / f'{name}.stop').write_text(info['token'], encoding='utf-8')
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if record(root, name).get('state') == 'stopped':
            handle = SUPERVISORS.pop(info['token'], None)
            if handle:
                handle.wait(timeout=3)
            return 'stopped'
        time.sleep(.2)
    raise RuntimeError(f'{name}_stop_unconfirmed')


if __name__ == '__main__' and len(sys.argv) == 4 and sys.argv[1] == '--serve':
    supervise(ROOT, sys.argv[2], sys.argv[3])
