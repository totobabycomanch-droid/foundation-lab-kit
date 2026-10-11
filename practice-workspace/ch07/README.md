# Chapter 7: 실패와 재시도 뒤 DB 상태 확인

개편 Core는 understanding/에서 Python 표준 sqlite3·unittest만 사용합니다.
외부 패키지 설치, HTTP 서버, 파일 DB, 반복 초기화는 필요하지 않습니다.
VS Code에서 understanding/을 열고 그 폴더의 README.md를 확인하세요.

생성 파일은 understanding/transaction_example.py, understanding/sale_example.py,
understanding/test_examples.py 세 개입니다. 기존 파일이 있으면 필요한 부분만 보완합니다.
이전 API 실습 안내와 의존성은 legacy-api/에 보관했습니다.
루트 requirements.txt는 이전 실습의 호환 자료이며 개편 Core에서는 설치하지 않습니다.
