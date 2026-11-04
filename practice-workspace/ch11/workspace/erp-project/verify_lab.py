"""이전 도구의 무표식 DB 쓰기를 차단하고 새 읽기 명령으로 연결한다."""
import sys

from lab import main


if __name__ == '__main__':
    aliases = {'inspect': 'inspect', 'state': 'state'}
    mode = sys.argv[1] if len(sys.argv) == 2 else ''
    if mode not in aliases:
        print('Not Run: legacy write commands are disabled. Use lab.py --help; case reset requires an explicit request.')
        raise SystemExit(1)
    raise SystemExit(main([aliases[mode]]))
