# Chapter 11 시작 위치

VS Code에서 이 ch11 폴더를 엽니다. [최신 원고](../../docs/11_chapter11.md)의 11.0-ENV부터 진행합니다.

- 백엔드: workspace/erp-project/
- 프론트엔드: workspace/frontend-project/
- 비교·복구 자료: 키트 루트의 chapter-reference/ch11/
- .env 연결값은 로컬에서만 입력하며 AI에게 전달하지 않습니다.
- DB 연결 주소의 시작은 postgresql+psycopg2://입니다. postgresql://만 쓰면 다른 드라이버를 찾을 수 있습니다.
- PowerShell 실행 정책으로 활성화가 차단돼도 원고의 venv Python 직접 실행 명령을 사용할 수 있습니다.

시작 폴더에는 완성 API·화면을 넣지 않습니다. AI 조사·생성 후 실행 결과를 직접 관찰해 기록하세요.


## Supabase 전용 프로젝트 준비

[공통 부록](../../docs/supplements/supabase_project_setup.md)에서 프로젝트 생성·Session pooler 주소·비밀번호 인코딩을 확인합니다.
장별 전용 DB를 사용하고, 준비 뒤 이 안내와 전자책의 해당 환경 설정 단계로 돌아갑니다.


## Chapter 11 진행 순서

[환경 준비](../../docs/supplements/ch11_environment_setup.md)를 마치고 [본문](../../docs/11_chapter11.md)의 11.1부터 진행합니다.
DB·API·화면의 결과를 확인한 직후 해당 핵심 코드를 읽고 observation_record.md의 같은 행에 결과·이유·코드 위치·판정을 적습니다.
최종 AI 검토와 업무 보고는 이 표를 재사용합니다. AI가 실제 관찰값을 대신 쓰게 하지 않습니다.
[선택 복습](../../docs/supplements/ch11_review.md)은 필요한 항목만 읽습니다. 기존 실습·SQL·관찰 기록은 덮어쓰지 않습니다.
