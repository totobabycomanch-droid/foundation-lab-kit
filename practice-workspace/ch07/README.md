# Chapter 7 실패와 재시도 뒤 DB 상태 확인

VS Code에서 understanding/을 열고 그 폴더의 README.md를 따릅니다.
Chapter 6에서 준비한 ch07/.venv의 Python 3.12를 사용합니다. 외부 패키지·Node.js·Docker·Supabase 설치는 필요하지 않습니다.
understanding/start_lab.ps1은 Python 표준 라이브러리의 로컬 웹 서버를 실행합니다. 기본 주소는 http://127.0.0.1:8307 입니다.
화면·연결·사례 준비·추적은 제공하고 transaction_example.py·sale_example.py의 업무 코드를 AI와 완성합니다.
test_examples.py에는 실습별 업무 검사를 작성합니다. 별도 제공 검사는 구현과 테스트의 누락을 함께 점검합니다.
시작본의 501과 업무 검사 미구현 안내는 정상입니다. 업무 함수의 트랜잭션은 제공 서버가 대신 구현하지 않습니다.
이전 API 실습과 의존성은 legacy-api/에 보존합니다. 루트 requirements.txt는 설치하지 않습니다.
