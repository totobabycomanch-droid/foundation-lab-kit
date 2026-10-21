# Chapter 6 작업 규칙

- 이 장에서는 도구와 실행 환경을 조사하며 업무 기능을 구현하지 않는다.
- 실제 `.env` 값은 읽거나 출력하지 않는다.
- Python, Node.js, npm과 Docker의 설치 여부를 각각 판정한다.
- 설치하지 않은 도구 때문에 실행할 수 없는 개별 검증은 `Not Run`으로 보고한다.
- `Not Run`은 개별 검증 결과에만 사용하며 성공 근거로 삼지 않는다. 환경 준비 상태와 구분한다.
- `environment_report.md`는 `Chapter 7 진입 필수 환경`과 `이후 사용할 환경`의 두 표로 작성한다.
  두 표의 열은 `항목 | 확인 기준 | 실제 확인 결과 | 상태 | 남은 조치 | 완료 시점·돌아갈 절`이다.
- 진입 필수 환경은 Python 3.12, ch07/.venv의 Python 3.12와 실행 경로, SQLite 조회·unittest import다.
  상태는 `Ready` 또는 `Needs Fix`만 허용한다. 미확인·미실행은 `Needs Fix`로 남긴다.
  ch07의 근거는 독자가 제공한 실행 결과로만 확인하며, 다른 Chapter를 읽거나 수정하지 않는다.
- 이후 환경은 Node.js·npm, Docker·Compose, Supabase다. `Ready`, `Needs Fix`, `Deferred`를 허용한다.
  `Ready`는 해당 행의 확인 기준을 충족하는 실제 근거가 있는 경우에만 사용한다.
  `Needs Fix`는 실패·기준 미달 또는 근거 부족인 경우다. 단, 이후 환경의 계획된 미착수는
  아래 `Deferred` 요건에 따라 구분한다.
  `Deferred`는 설치·실행 확인을 아직 시작하지 않았고 미착수 사유와 보완 계획이 있는 경우다.
- 실패한 항목은 수리를 미루더라도 `Needs Fix`를 유지하며 `Deferred`로 바꾸지 않는다.
  미완료 항목에는 오류 또는 미착수 사유, 남은 조치, 완료 시점과 돌아갈 절을 기록한다.
- 준비 완료 시점과 복귀 위치는 Node.js·npm은 Chapter 11 시작 전·6.1 Node.js 절,
  Docker·Compose는 Day 00 시작 전·6.1 Docker 절, Supabase는 Chapter 10 Supabase 준비 절이다.
  Docker의 `Ready`에는 WSL 최소 요구사항과 CLI·Client·Server·Compose v2의 근거가 필요하다.
- Supabase는 Chapter 5 SQL Editor 실습 이력에 한해 `Ready`를 기록한다. 이력이 없고 보완 계획이
  있으면 `Deferred`, 실제 접속 오류가 제공되면 `Needs Fix`다. Chapter 10의 현재 연결을 추측하지 않는다.
- 진입 필수 환경이 모두 `Ready`이고 환경 문서의 AI 검증·독자 자가 체크를 마치면 Chapter 7 진행이
  가능하다. 이후 환경이 미완료여도 Chapter 7을 막지 않으며, 사용할 장을 시작하기 전에는 보완한다.
  모든 도구가 `Ready`일 때만 전체 도구 준비 완료로 표현한다.
