"""AI가 호출하는 ch11 실행 CLI. python lab.py --help로 명령을 확인한다."""
import argparse
import importlib.util
import json
import shutil
import subprocess
import sys

import lab_db as db
import lab_servers as servers


def environment():
    node = shutil.which('node')
    version = None
    if node:
        result = subprocess.run([node, '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
    modules = {name: bool(importlib.util.find_spec(name))
               for name in ('dotenv', 'sqlalchemy', 'psycopg2', 'fastapi', 'uvicorn')}
    config = 'Not Run'
    if all(modules[name] for name in ('dotenv', 'sqlalchemy')):
        try:
            db.settings()
            config = 'Pass'
        except db.LabError as error:
            config = str(error)
    front = db.ROOT.parent / 'frontend-project'
    return {'python': sys.version.split()[0], 'python_312': sys.version_info[:2] == (3, 12),
            'modules': modules, 'node': version, 'npm_available': bool(shutil.which('npm.cmd' if sys.platform == 'win32' else 'npm')),
            'frontend_dependencies': (front / 'node_modules/vite/bin/vite.js').is_file(),
            'local_settings': config, 'database_connection': 'Not Run'}


def database_command(args):
    # 파일 경로·내용 검사는 DB에 연결하기 전에 끝낸다.
    source = db.sql_source(args.file) if args.command == 'apply' else None
    with db.connection() as cur:
        if args.command == 'init':
            db.initialize(cur)
            result = {'marker': 'prepared'}
        elif args.command == 'apply':
            result = {'sql': db.apply_sql(cur, *source)}
        elif args.command == 'prepare':
            keys = tuple(db.CASES) if args.case == 'all' else (args.case,)
            result = {key: db.prepare_case(cur, key, args.reset) for key in keys}
        elif args.command == 'state':
            result = {'orders': db.state(cur)}
        elif args.command == 'clear-database':
            result = db.clear_database(cur)
        else:
            result = db.inspect(cur)
    # commit 성공 후에만 적용 성공을 출력한다.
    return result


def parser():
    p = argparse.ArgumentParser(description='Chapter 11 dedicated lab tools')
    commands = p.add_subparsers(dest='command', required=True)
    for name in ('env', 'init', 'inspect', 'state', 'resume'):
        commands.add_parser(name)
    apply = commands.add_parser('apply', help='Apply a reviewed schema file inside backend sql/')
    apply.add_argument('file')
    prepare = commands.add_parser('prepare', help='Create missing reader cases; preserve existing results')
    prepare.add_argument('--case', choices=('A', 'B', 'all'), default='all')
    prepare.add_argument('--reset', action='store_true', help='Explicitly reset only the selected reader case(s)')
    clear = commands.add_parser('clear-database', help='Remove Chapter 11 tables, functions, marker and SQL history')
    clear.add_argument('--confirm', required=True, choices=('CHAPTER11',), help='Explicit consent to discard all Chapter 11 DB results')
    server = commands.add_parser('servers')
    server.add_argument('action', choices=('status', 'start', 'stop', 'logs'))
    server.add_argument('--service', choices=('api', 'web', 'all'), default='all')
    return p


def run(args):
    if args.command == 'env':
        return environment()
    if args.command == 'servers':
        names = tuple(servers.PORTS) if args.service == 'all' else (args.service,)
        if args.action == 'status':
            return {name: servers.status()[name] for name in names}
        if args.action == 'logs':
            result = {}
            for name in names:
                path = servers.runtime(db.ROOT) / f'{name}.log'
                result[name] = path.read_text(encoding='utf-8') if path.is_file() else 'Not Run'
            return result
        if args.action == 'start':
            if 'api' in names:
                db.settings()
            return {name: servers.start(name) for name in names}
        return {name: servers.stop(name) for name in names}
    if args.command == 'resume':
        result = {'servers': servers.status()}
        try:
            result['database'] = database_command(argparse.Namespace(command='inspect'))
            result['orders'] = database_command(argparse.Namespace(command='state'))['orders']
        except Exception as error:
            result['database_remaining'] = safe_error(error)
        return result
    return database_command(args)


def safe_error(error):
    if isinstance(error, db.LabError):
        return {'result': 'Not Run', 'reason': str(error)}
    if isinstance(error, (ModuleNotFoundError, ImportError)):
        return {'result': 'Not Run', 'reason': 'dependencies_missing'}
    if isinstance(error, RuntimeError) and str(error) in {
        'api_implementation_missing', 'frontend_dependencies_missing',
        'api_port_in_use_no_process_stopped', 'web_port_in_use_no_process_stopped',
        'api_startup_failed_check_sanitized_logs', 'web_startup_failed_check_sanitized_logs',
        'api_stop_unconfirmed', 'web_stop_unconfirmed',
    }:
        return {'result': 'Fail', 'reason': str(error)}
    # 드라이버 예외 본문에는 URL·비밀번호가 포함될 수 있어 출력하지 않는다.
    sqlstate = getattr(error, 'pgcode', None)
    return {'result': 'Fail' if sqlstate else 'Not Run', 'reason': 'database_or_tool_operation_failed',
            'exception_type': type(error).__name__}


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as error:
        print(json.dumps(safe_error(error), ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 1 if args.command == 'resume' and 'database_remaining' in result else 0


if __name__ == '__main__':
    raise SystemExit(main())
