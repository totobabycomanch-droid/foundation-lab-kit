# Chapter 11 환경 준비와 실행 도움말

처음 시작한다면 [본문의 환경 준비](../11_chapter11.md#ch11-environment)를 마치고
[11.2의 구현 요청](../11_chapter11.md#ch11-api-prepare)을 실행합니다.
이 문서는 설치·연결 문제가 있거나 실습을 중단했다가 돌아왔을 때 필요한 항목만 찾아보는 도움말입니다.

## 누가 무엇을 준비하나요?

| 독자 | AI |
|---|---|
| VS Code에서 키트의 `practice-workspace/ch11/` 열기 | 규칙과 연결 명세·현재 파일 조사 |
| Python 3.12·Node.js 실행 기반 준비 | 프로젝트 가상환경·기존 의존성 설치 확인 |
| 새 전용 Supabase 프로젝트 생성·로컬 `.env` 설정 | 대상 대조·접속 확인·SQL 작성과 적용 |
| 업무 조건 결정·화면과 저장 결과 판단 | 별도 테스트 데이터로 검사·관리 서버 실행 |

AI는 실제 `.env`를 열거나 출력하지 않습니다. 제공 도구·API·검사 프로세스가 로컬 연결값을 사용하는 것은 허용됩니다.
연결값이나 오류 전문을 대화에 붙여 넣을 필요는 없습니다.

<a id="ch11-python-setup"></a>
<a id="ch11-existing-venv"></a>
<a id="ch11-python-help"></a>

## Python·Node.js 설치가 막혔을 때

Python 자체를 찾을 수 없다면 [6장의 Python 준비](../book_navigation.md#chapter6#ch6-python-ready)부터 확인합니다.
Node.js·npm을 찾을 수 없다면 [6장의 Node.js 준비](../book_navigation.md#chapter6#nodejs-ready)로 돌아갑니다.
프로젝트 패키지 설치 문제는 AI가 기존 `requirements.txt`와 npm 잠금 파일, 실행 결과를 조사하게 합니다.

```text
현재 프로젝트의 Python·Node.js 실행 기반과 설치 실패 원인을 조사해 주세요.
기존 가상환경의 버전과 실행 경로를 확인하고, 맞는 환경은 재사용해 주세요.
기존 의존성 파일로 설치하고 실제 결과를 확인해 주세요. 버전을 임의 변경하거나 기존 환경을 삭제하지 마세요.
추가 시스템 설치나 기존 파일 변경이 필요하면 이유와 범위를 먼저 알려 주세요.
```

Windows에서 가상환경 활성화가 차단돼도 시스템 실행 정책을 바꿀 필요는 없습니다.
AI가 `venv/Scripts/python.exe`를 직접 지정해 실행할 수 있습니다.
`npm.ps1` 실행이 차단되면 `npm.cmd`를 사용합니다.
macOS·Linux에서는 해당 가상환경의 `venv/bin/python`을 사용합니다.

## 전용 DB 설정과 연결 문제

<a id="ch11-supabase-project"></a>
<a id="ch11-db-check"></a>
<a id="ch11-db-connection-help"></a>

설정은 백엔드 `workspace/erp-project/.env`의 두 값입니다.
`DATABASE_URL`은 전용 프로젝트의 DB 연결 주소이고, `CH11_PROJECT_REF`는 같은 프로젝트의 20자리 참조 ID입니다.
ID를 찾는 위치와 입력 방법은 [본문의 연결 준비](../11_chapter11.md#ch11-supabase-project)를 따릅니다.

제공 도구는 연결 URL의 호스트 또는 Session pooler 사용자와 참조 ID를 대조합니다.
DB 이름 `postgres`, 포트 `5432`, TLS 암호화 연결을 사용합니다.
이 확인만으로 프로젝트가 폐기 가능한 전용 실습용인지까지 알 수는 없으므로, 독자가 프로젝트 용도를 확인해야 합니다.

아래는 실제 도구가 표시하는 결과와 다음 행동입니다. `env` 검사는 형식을 확인하며 DB에는 접속하지 않습니다.

| 결과·이유 코드 | 의미와 다음 행동 |
|---|---|
| `local_settings_required` | 두 값 누락 또는 참조 ID 형식 문제. 독자가 로컬 `.env`를 확인하고 저장 |
| `dedicated_target_mismatch` | URL·참조 ID 불일치나 지원하지 않는 연결 형식. 같은 프로젝트의 Session pooler·5432인지 확인 |
| `OperationalError` | 접속 단계 문제. 프로젝트 일시 중지·네트워크·비밀번호 처리를 확인한 뒤 도구로 재검사 |
| `marker_missing_run_init` | 초기 표식 없음. AI가 빈 전용 DB 조건을 확인하고 `init` 수행 |
| `existing_objects_preserved`·`existing_function_preserved` | 기존 객체 발견. 삭제하지 말고 새 실습 DB인지와 기존 작업 보존 범위를 확인 |
| `history_missing_use_fresh_database`·`untracked_objects_preserved` | SQL 적용 이력과 실제 객체를 안전하게 연결할 수 없음. 자동 채택·전체 초기화 없이 차이 보고 |
| `applied_sql_changed_use_new_file` | 이미 적용한 SQL 파일 내용이 달라짐. AI가 적용 이력과 필요한 후속 변경을 조사 |
| `schema_not_ready_existing_data_preserved` | 필요한 테이블·필드가 준비되지 않음. 적용 결과부터 확인하며 기존 데이터 보존 |
| `case_identity_conflict`·`product_identity_conflict`·`product_shared_with_other_order` | 사례의 주문·상품이 예상과 다름. 재준비를 반복하지 말고 충돌 대상 조사 |

프로젝트가 일시 중지됐다면 Supabase 대시보드에서 해당 전용 프로젝트를 재개합니다.
비밀번호나 참조 ID를 수정한 뒤에는 값을 대화로 보내지 말고 “로컬 설정을 수정했으니 연결을 다시 확인해 주세요”라고 요청합니다.

## 중단 후 다시 시작하기

<a id="ch11-resume"></a>

같은 `ch11/` 폴더를 열고 다음처럼 요청합니다.

```text
프로젝트 규칙을 읽고 현재 SQL 적용 이력·DB의 두 주문·서버 상태를 조사해 중단한 실습을 이어서 진행해 주세요.
기존 코드와 관찰 결과를 보존하고, 필요한 설치·적용·서버 실행만 수행해 주세요.
이미 승인된 주문은 다시 승인하거나 자동 초기화하지 말고 현재 상태와 화면 주소를 알려 주세요.
```

`lab.py resume`은 상태를 읽는 도구이며 서버 시작·재시작이나 DB 초기화를 하지 않습니다.
AI가 이 결과로 남은 작업을 판단합니다. A가 이미 `PAID`·재고 7·원장 1건이라면
정상 승인을 다시 실행하지 않고 [B 확인](../11_chapter11.md#ch11-check-shortage)부터 이어갈 수 있습니다.

<a id="ch11-experiment-states"></a>

| 진행 상태 | A | B | 이어갈 곳 |
|---|---|---|---|
| 구현·준비 완료 | 수량 1·CREATED·재고 10·원장 0건 | 수량 1·CREATED·재고 2·원장 0건 | A의 수량 3 입력·저장 후 승인 |
| A 승인 완료 | 수량 3·PAID·재고 7·원장 1건(-3) | 수량 1·CREATED·재고 2·원장 0건 | B의 수량 3 입력·저장 후 승인 요청 |
| B 거절 확인 완료 | A 결과 유지 | 수량 3·CREATED·재고 2·원장 0건 유지 | 코드 흐름 이해·완료 |

이 표는 기대 상태입니다. 실제 DB를 조회하지 않고 이미 완료했다고 판단하지 않습니다.
수량 저장 직후 중단했다면 저장된 수량 3과 각 주문의 승인 대기·시작 재고를 확인하고 승인 단계부터 이어갑니다.
응답을 못 받았다면 먼저 저장 상태를 확인합니다. 화면의 과거 표시값만 보고 재요청하지 않습니다.

## 서버·화면 실행 문제

<a id="ch11-run-help"></a>
<a id="ch11-ai-debug-help"></a>

기대와 실제 차이를 한 문장 덧붙이고 AI에게 조사·수정·관련 검사까지 요청합니다.

```text
현재 화면이 열리지 않습니다. 프로젝트 규칙과 현재 코드·관리 서버 상태·연결값을 가린 로그를 조사해 주세요.
원인을 확인해 허용 범위 안에서 수정하고, 관련 검사와 실제 접속을 다시 확인해 주세요.
다른 프로그램을 종료하거나 기존 DB 결과를 초기화하지 마세요. 남은 문제와 화면 주소를 짧게 알려 주세요.
```

| 증상 | AI가 확인할 것 |
|---|---|
| 포트 사용 중 | 관리 서버 재사용 여부와 다른 프로세스 점유 구분. 다른 프로세스는 임의 종료하지 않음 |
| `api_implementation_missing` | 생성된 API와 실행 위치 확인. 실행 기반만 있는 것을 기능 완성으로 보고하지 않음 |
| `frontend_dependencies_missing` | 기존 잠금 파일로 패키지 설치가 끝났는지 확인 |
| `api_startup_failed_check_sanitized_logs` 등 | 연결값을 가린 관리 로그와 실제 시작 실패 위치 확인 |
| 화면은 열리지만 조회 실패 | API·DB 연결, 표식·스키마와 실제 `GET /orders` 응답 확인 |
| CORS·404·422 | 화면 주소와 API 허용 출처·요청 경로·입력 필드 확인 |
| 저장 성공 뒤 조회 실패 | 저장 취소로 단정하지 않고 현재 저장 상태 재조회 |
| 응답 없음·시간 초과 | 처리 결과 미확인으로 구분하고 DB 상태부터 확인 |

기본 화면 주소는 `http://localhost:5173`, API는 `http://localhost:8000`입니다.
브라우저에서 `localhost`를 다른 호스트 이름으로 바꾸면 허용 출처와 달라질 수 있으므로 AI가 확인한 주소를 사용합니다.

### 필요한 경우에만 도구를 직접 실행하기

보통 AI가 실행합니다. 직접 상태를 확인해야 할 때만 **백엔드 폴더**에서 아래 읽기 명령을 사용합니다.
이미 Python 3.12 가상환경과 패키지가 준비된 경우의 Windows PowerShell 예입니다.

```powershell
& .\venv\Scripts\python.exe lab.py env
& .\venv\Scripts\python.exe lab.py resume
```

서버를 종료할 때는 AI에게 관리 서버만 종료하도록 요청합니다. 도구가 관리하는 두 서버를 직접 종료하려면 다음을 실행합니다.

```powershell
& .\venv\Scripts\python.exe lab.py servers stop
```

API·웹을 구분해야 할 때는 `--service api` 또는 `--service web`을 붙입니다.
전체 명령 설명은 키트의 `practice-workspace/ch11/README.md`에 있습니다.

<a id="ch11-prepare-case"></a>

## 같은 사례를 다시 확인하고 싶을 때

Core에서는 A와 B 사이에 재준비가 필요하지 않습니다.
복습을 위해서만 “A만 시작 상태로 재준비해 주세요”처럼 대상을 지정합니다.
AI는 현재 결과를 먼저 확인하고 해당 주문·상품·원장만 복원합니다.

수동 실행이 꼭 필요하다면 기존 결과를 보존한 뒤, 전용 DB 대상과 A를 되돌릴 의도를 확인하고 다음 명령을 사용합니다.

```powershell
& .\venv\Scripts\python.exe lab.py prepare --case A --reset
& .\venv\Scripts\python.exe lab.py state
```

A는 수량 1·`CREATED`·재고 10·원장 0건으로 돌아갑니다. B만 복습하려면 `--case B`를 지정하며 수량 1·시작 재고 2로 돌아갑니다.
각 사례를 다시 확인할 때는 수량을 3으로 입력·저장한 뒤 승인합니다.
원장 증감량은 행이 없으므로 `NULL`입니다. 화면도 다시 조회해 저장 상태와 맞춥니다.

이 작업은 코드 초기화와 다릅니다. 키트의 `reset_practice_chapter.ps1`은 코드 복원 도구이며 DB 결과를 되돌리지 않습니다.
`workspace/sql/99_reset_lab.sql`은 테이블·함수를 삭제하는 별도 도구로, 두 사례의 재준비나 중단 후 재개에 사용하지 않습니다.
기존 SQL 적용 이력까지 되돌리는 도구도 아니므로, 재실습을 위해 임의 실행하지 않습니다.

[본문으로 돌아가기](../11_chapter11.md#ch11-after-environment)
