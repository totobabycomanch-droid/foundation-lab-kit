# Chapter 11. DB-API-화면 3층 연동 실습: 설계를 동작하는 코드로

> **실습 키트:** [기초 실습 환경 준비](01A_foundation_lab_setup.md#kit-download)
> 아직 준비하지 않았다면 [기초 실습 환경 준비](01A_foundation_lab_setup.md)를 먼저 완료하세요.

## 11.0 이 챕터에서 얻는 것

주문 승인 한 건을 DB 함수 → FastAPI → Vue 화면으로 연결합니다. 전체 문법을 외우기보다
요청 검사·저장·응답이 이어지는 위치와 실제 결과를 확인하세요.
이 장의 `PAID`와 화면의 `isPaid`는 승인 완료를 나타내는 실습용 이름이며, 실제 결제 연동은 포함하지 않습니다.

이 장을 마치면 다음을 할 수 있습니다.

- 승인 요청이 DB·API·화면을 통과하는 경로를 실제 코드에서 찾습니다.
- 성공 표시를 API 응답과 주문·재고·원장의 저장 결과로 확인합니다.
- 실패가 거절된 위치와 바뀌지 않아야 할 데이터를 설명합니다.
- 업무 요청에서 빠진 조건을 보완하고, AI의 검토 중 확인된 사실과 미검증 주장을 구분합니다.

### [진행 기준] 실습 단계별 완료 결과

| 경로 | 할 일 | 다음으로 넘어갈 기준 |
| :--- | :--- | :--- |
| **Core 준비 (11.0-ENV~11.1)** | 시작 키트·의존성·DB 연결값 준비 | 두 서버를 실행할 준비가 됨 |
| **Core DB (11.2)** | 테이블·함수 생성 후 정상 승인 실행 | 주문·재고·원장 결과 확인 후 시작 상태 복원 |
| **Core API (11.3)** | Swagger(브라우저에서 API를 시험하는 화면)에서 승인 요청 | 성공 응답과 DB 저장 결과 일치 |
| **Core 화면 (11.4~11.5)** | API 연결과 화면 상태 처리 | 요청·로딩 잠금·성공 표시 확인 |
| **Core 검증·완료 (11.6·11.8)** | 실패·재시도·입력 오류 실행, AI 검토와 직접 대조 | 관찰 기록과 최종 자가 체크 완료 |
| **Core 종료 (11.9~11.10)** | 서버 종료·결과 보존, 요약 확인 | Chapter 11 결과를 남기고 Day 00으로 이동 |
| **선택 복습 (11.7·11.11~11.13)** | 방어 장치·참조 코드·구조의 한계·Day 프로젝트 미리보기 | Core 완료 후 필요한 주제만 읽기 |

표의 **Core**는 이 장을 끝내는 데 꼭 필요한 필수 경로를 뜻합니다.
중간에 멈출 때는 사용한 코드와 마지막 실행 결과를 남깁니다. 각 절의 **[반드시 따라하기]**가
필수 실습이며, **[읽어만 보기]·[선택 읽기]·[시니어용]**과 심화 프롬프트는 선택 복습입니다.
DB 함수·FastAPI·Vue 연동을 이미 직접 검증할 수 있다면 이 장을 건너뛰어도 됩니다.

한 번에 끝내지 않아도 됩니다. **환경 준비 → DB 승인 성공 → API 승인 성공 → 화면과 검증**의
네 구간으로 나누어 진행하세요. 각 구간의 완료 기준을 확인한 뒤 멈추고, 다음에는 아래 재개 절차를 따릅니다.

학습 시간을 잡을 때는 명령 실행뿐 아니라 AI의 조사·생성, 코드 확인, 오류 해결과 관찰 기록까지
포함하세요. 설치 상태와 네트워크, AI의 응답에 따라 걸리는 시간이 다르므로 위 표의 완료 기준으로
진도를 판단합니다. 환경 준비만 별도 세션으로 진행해도 됩니다. 이후에도 한 구간씩 결과를 확인하고 쉬어 가세요.

> [!NOTE]
> 이 장은 Vue **Options API**(`data()`와 `methods`로 상태와 함수를 나누어 쓰는 방식)로 단일 화면을 연결합니다. Day 프로젝트의 Composition API는
> 11.9의 선택 미리보기에서 볼 수 있습니다. 지금 두 방식을 함께 구현할 필요는 없습니다.

**중단 후 다시 시작할 때**

멈추기 전에는 마지막으로 완료한 STEP, 사용한 SQL 실행본과 코드를 보존하고,
마지막 응답·DB 상태·다음에 할 실험을 [관찰 기록](#ch11-manual-record)에 적습니다. 연결값은 기록하지 않습니다.
SQL 실행본은 [11.2의 보존 절차](#ch11-sql-record)에 따라 백엔드의 `sql/` 폴더에 남깁니다.
다시 시작할 때는 다음 순서로 확인하세요.

1. VS Code에서 기존 `practice-workspace/ch11/`을 열고 마지막 완료 STEP과 다음 실험을 확인합니다.
   설치를 마쳤다면 `npm ci`·가상환경 생성·패키지 설치를 처음부터 반복할 필요는 없습니다.
2. Chapter 11 전용 Supabase 프로젝트가 활성 상태인지 확인합니다. 일시 중지됐다면 대시보드에서
   해당 프로젝트를 선택해 **Resume project**로 재개하고, 11.0-ENV 5단계의 연결 확인을 다시 합니다.
   복원 방법과 가능 기간은 [공식 일시 중지 안내](https://supabase.com/docs/guides/platform/free-project-pausing)를 확인하세요.
3. 11.2에서 테이블과 고정 주문까지 만들었다면 [상태 조회](#ch11-state-query)로 현재 값을 읽습니다.
   새 실험은 해당 절에서 요구하는 시작 상태로 맞춥니다. 아직 생성하지 않은 객체의 조회·초기화는 실행하지 않습니다.
4. API 실험부터는 11.3의 백엔드 실행 절차를, 화면 실험부터는 11.4의 프론트엔드 실행 절차도 따릅니다.
   새 백엔드 터미널에서도 기존 `venv`의 Python을 직접 사용하고, 안내대로 현재 터미널의 `DATABASE_URL`만 해제합니다.
   서버가 이미 실행 중이라면 중복 실행하지 않습니다.
5. 새 화면 실험은 DB 시작 상태를 확인한 뒤 페이지를 새로고침합니다. 단, 11.6의 **같은 화면에서 재시도**는
   오류 화면을 유지한 채 DB만 복원합니다. 브라우저를 닫아 오류 화면이 사라졌다면 재고 부족 실험부터 다시 수행합니다.

기록과 현재 값이 다르면 승인 요청을 추가로 보내지 말고 마지막 실행 결과부터 확인합니다.
DDL을 다시 실행하거나 전체 초기화로 돌아가기 전에, 멈춘 단계의 **[막혔을 때]** 안내를 확인하세요.

---

## 11.0-ENV 실습 시작 전 환경 구축 (Chapter 11 Supabase 전용)

VS Code에서 기초 실습 키트의 `practice-workspace/ch11/`만 엽니다. `workspace/erp-project/`는
백엔드, `workspace/frontend-project/`는 프론트엔드입니다. Chapter 10의 `erp-mini/`는 복사하지 않습니다.
이 폴더와 DB는 Chapter 11 전용이며, Day 00에서는 별도 저장소를 새 폴더에 준비합니다.

Node.js와 npm은 Chapter 6에서 준비한 환경을 사용합니다. `node --version`이나 `npm --version`이
실행되지 않으면 [Node.js 준비 절](06_chapter6.md#nodejs-ready)에서 해결한 뒤 돌아오세요.

이번 준비는 **시작 파일 확인 → 실행 도구 설치 → 전용 DB 연결** 순서로 진행합니다.
1~3단계를 마치면 로컬 실행 준비가 끝나고, 4~5단계를 마치면 DB까지 연결됩니다.
두 서버를 켜거나 주문 승인 결과를 확인하는 일은 뒤의 실습에서 진행합니다.

#### 1단계. 시작 scaffold 확인

scaffold는 실습을 시작할 파일과 폴더의 뼈대입니다. PowerShell에서 키트 루트로 이동해 확인합니다.
실제 설치 위치가 다르면 아래 경로를 자신의 위치로 바꾸세요.

```powershell
Set-Location C:\erp-book\foundation-lab-kit
./tools/verify_practice_chapter.ps1 -Chapter ch11
Set-Location practice-workspace/ch11

Test-Path AGENTS.md
Test-Path workspace/erp-project/api/__init__.py
Test-Path workspace/erp-project/.env.example
```

DB 실행 항목의 `Not Run`(실행하지 않아 아직 판정하지 않았다는 표시)은 오류가 아닙니다. 도구는 DB에 자동 접속하지 않습니다.
세 `Test-Path` 결과는 모두 `True`여야 합니다. 하나라도 `False`라면 키트를 새 폴더에 다시
압축 해제해 시작 파일을 확인합니다. 기존 작업이 있는 폴더에 덮어쓰지 않습니다.

#### 2단계. 프론트엔드 의존성 설치

같은 터미널에서 실행합니다. 제공된 `package.json`과 잠금 파일을 사용하며 새 Vite 프로젝트를 만들지 않습니다.

```powershell
Set-Location workspace/frontend-project
npm ci
```

#### 3단계. 백엔드 가상환경과 의존성 설치

새 터미널에서 백엔드 폴더로 이동해 실행합니다. 이 장은 가상환경 안의 Python을 직접 지정하므로
활성화 스크립트가 실행 정책으로 차단돼도 같은 명령으로 실습을 이어갈 수 있습니다.

```powershell
Set-Location C:\erp-book\foundation-lab-kit\practice-workspace\ch11\workspace\erp-project
python -m venv venv
Test-Path .\venv\Scripts\python.exe
& .\venv\Scripts\python.exe --version
& .\venv\Scripts\python.exe -c "import sys; print(sys.executable)"
& .\venv\Scripts\python.exe -m pip install -r requirements.txt
```

`Test-Path`가 `True`이고, 출력된 실행 경로가 `ch11\workspace\erp-project\venv\Scripts\python.exe`로
끝나는지 확인합니다. `False`라면 현재 위치와 가상환경 생성 시의 최초 오류부터 확인하세요.
기존 환경을 삭제하거나 재설치하기 전에 [6장의 가상환경 준비·오류 진단](06_chapter6.md#ch6-verify-venv)을 참고합니다.
6장의 `.venv`와 달리 이 장의 폴더 이름은 `venv`입니다.

macOS·Linux에서는 같은 폴더에서 `python3 -m venv venv`로 만들고,
`./venv/bin/python -m pip install -r requirements.txt`로 설치합니다. 이후 Python 실행에도
Windows의 `& .\venv\Scripts\python.exe` 대신 `./venv/bin/python`을 사용합니다.

활성화는 선택입니다. PowerShell에서 `.\venv\Scripts\Activate.ps1`을 실행하면 아래 그림처럼
`(venv)`가 표시될 수 있지만, 표시 여부는 완료 조건이 아닙니다. 실행 정책으로 차단되면 정책을
변경하지 않고 위의 Python 직접 실행 방식을 사용하세요.

![가상환경 활성화 터미널 예시](images2/11_chapter11_venv_terminal.png)

`requirements.txt`에는 FastAPI·Uvicorn·SQLAlchemy·psycopg2-binary·python-dotenv가 들어 있습니다.
설치에 실패하면 의존성 파일을 바꾸기 전에 오류 메시지와 가상환경·네트워크·Python 버전을 확인합니다.

**여기까지의 완료 기준:** 시작 파일 확인과 `npm ci`·`pip install`이 모두 성공했다면 로컬 준비는 끝났습니다.
잠시 멈춘다면 마지막 완료 단계를 기록하세요. 다음에는 백엔드 폴더에서 기존 `venv`의 Python을 사용해 4단계부터 이어갑니다.

#### 4단계. Supabase 연결 정보 설정

**Chapter 11 전용 프로젝트 준비:** 이 장에서는 5장·10장의 프로젝트를 재사용하지 않고
별도 Supabase 프로젝트를 새로 만듭니다. 이미 Chapter 11 전용 프로젝트를 만들었다면
다시 생성하지 말고 그 프로젝트를 사용합니다.

**무료 프로젝트 한도 때문에 생성할 수 없다면:** 무료 플랜은 활성 프로젝트 2개까지 사용할 수 있으며,
일시 중지된 프로젝트는 이 한도에 포함되지 않습니다. 조직의 Owner·Admin 구성원 사용량도 영향을 줍니다.
현재 조건은 [Supabase 요금 FAQ](https://supabase.com/docs/guides/platform/billing-faq)를 확인하세요.

- 먼저 이전 장의 SQL 실행본·코드·관찰 결과를 로컬에 보존합니다. DB 데이터 자체도 계속 보관해야 한다면
  일시 중지를 장기 백업으로 여기지 말고 [공식 백업 안내](https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore)를 확인합니다.
- 현재 사용하지 않는 **자신의 무료 실습 프로젝트**를 선택하고,
  **Settings → General → Project availability → Pause Project**에서 일시 중지한 뒤 새 프로젝트 생성을 다시 시도합니다.
  메뉴 위치는 [공식 프로젝트 관리 안내](https://supabase.com/docs/guides/platform/delete-project#alternative-pause-your-project)에서 확인할 수 있습니다.
- 중지할 수 있는 실습 프로젝트가 없거나 한도가 계속 표시되면 조직 구성원과 플랜 조건부터 확인합니다.
  기존 DB에 11장 SQL을 섞어 실행하거나, 한도를 해결하려고 이전 프로젝트를 삭제할 필요는 없습니다.

1. [Supabase 대시보드](https://supabase.com/dashboard)에 로그인하고 새 프로젝트를 만듭니다.
   사용할 조직을 선택하고 이름은 `erp-chapter11-lab`처럼 실습 용도를 알아볼 수 있게 정합니다.
2. DB 비밀번호를 설정해 안전한 곳에 보관하고, 사용할 지역을 선택해 생성을 완료합니다.
   프로젝트가 준비된 뒤 해당 프로젝트의 SQL Editor와 Connect 화면을 열 수 있는지 확인합니다.
3. 화면의 프로젝트 이름을 확인합니다. 뒤의 SQL Editor 작업과 백엔드 연결은 모두 이 프로젝트를 대상으로 합니다.
   5장·10장·Day 프로젝트의 연결값을 복사하지 않습니다.

Supabase 프로젝트를 만들면 PostgreSQL DB가 함께 준비됩니다. 별도의 `CREATE DATABASE` 명령은
실행하지 않습니다. 이 장에서 사용할 테이블과 승인 함수는 11.2에서 만듭니다.

**로컬 연결 설정:**

백엔드 터미널에서 다음 명령을 실행합니다. 이미 `.env`를 작성했다면 복사 명령은 생략합니다.

```powershell
Copy-Item .env.example .env
```

설정 파일은 `ch11/` 기준 `workspace/erp-project/.env`입니다. 키트 루트나 프론트엔드의 `.env`와 구분합니다.
이 파일에 `DATABASE_URL` 한 줄을 채우는 것이 4단계의 마지막 작업이며, 세 가지만 지키면 됩니다.

1. **복사 위치:** 앞에서 준비한 **Chapter 11 전용 프로젝트**의 **Connect → Session pooler → URI**를 복사합니다.
   사용자명·호스트·포트는 직접 조합하지 말고, 이 화면의 값을 통째로 가져옵니다.
2. **시작 부분만 수정:** 주소의 `postgresql://`를 `postgresql+psycopg2://`로 바꿉니다.
   이 장에서 설치한 `psycopg2-binary` 드라이버를 쓰겠다고 지정하는 표기입니다.
3. **비밀번호:** 프로젝트를 만들 때 정한 DB 비밀번호를 넣습니다. 비밀번호에 `@`, `#`, `/` 같은
   특수문자가 있으면 URL 인코딩이 필요합니다. 이는 주소의 구분자로 해석될 문자를 `%40` 같은 표기로 바꾸는 것입니다.

**비밀번호에 특수문자가 있을 때:** 백엔드 폴더의 로컬 터미널에서 아래 명령을 직접 실행합니다.
AI에게 실행을 맡기지 말고, `DB password:`가 나오면 인코딩하지 않은 원래 비밀번호를 입력하세요.
입력한 글자는 화면에 나타나지 않습니다. 입력 숨김을 지원하지 않는 환경에서는 오류로 중단됩니다.

```powershell
& .\venv\Scripts\python.exe -c "
import warnings
from getpass import getpass, GetPassWarning
from urllib.parse import quote
warnings.simplefilter('error', GetPassWarning)
print(quote(getpass('DB password: '), safe=''))
"
```

출력값으로 URI의 **비밀번호 부분만** 바꿉니다. 예를 들어 가짜 비밀번호 `lab@/#`는
`lab%40%2F%23`으로 바뀝니다. 주소 전체나 이미 인코딩한 값을 다시 변환하지 않습니다.
인코딩은 암호화가 아니므로 출력값도 비밀정보입니다. 자신의 `.env`에만 옮기고,
AI 대화·Git·화면 캡처에 포함하지 않습니다. 자세한 동작은 [Python URL 인코딩 안내](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.quote)를 참고하세요.

Connect 창에서 Session pooler와 URI를 고르면 다음과 같은 화면이 나옵니다. 호스트와 사용자명은
프로젝트마다 다르므로 자신의 화면에서 확인한 값을 사용하세요.

![Connect 창에서 Session pooler와 URI를 선택한 연결 정보 화면](images2/11_chapter11_supabase_connect_pooler.png)

```dotenv
# 형식 예시입니다. USER·PASSWORD·HOST·PORT는 공식 연결 화면의 자신의 값으로 바꿉니다.
DATABASE_URL="postgresql+psycopg2://USER:PASSWORD@HOST:PORT/postgres"
```

자세한 형식은 [Supabase 연결 안내](https://supabase.com/docs/guides/database/connecting-to-postgres)와
[SQLAlchemy psycopg2 연결 명세](https://docs.sqlalchemy.org/en/21/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg2)를 참고합니다.
실제 `.env`와 비밀값은 AI가 읽거나 출력하지 못하게 하고, 채팅·Git·화면 캡처에도 포함하지 않습니다.

접속 대상의 프로젝트 이름과 보존할 데이터 유무를 직접 확인한 뒤,
`ch11/` 기준 `workspace/sql/00_initialize_lab.sql` 전체를 Supabase SQL Editor에서 한 번 실행합니다.
이 SQL은 업무 테이블을 만들지 않고 전용 실습 DB 표식만 기록합니다. 장 끝의 객체 제거 SQL은
표식이 없으면 중단되지만, 표식 자체가 DB의 용도를 판별하지는 않습니다. 운영 DB나 Day 프로젝트에 실행하지 않습니다.

#### 5단계. DB 연결 확인

백엔드 터미널(`erp-project/` 폴더)에서 기존 `venv`의 Python으로 연결만 확인합니다.

아래 첫 명령은 이 장에서 서버를 실행할 때마다 반복됩니다. 이유는 한 가지입니다.
`load_dotenv()`는 터미널에 이미 `DATABASE_URL`이 있으면 `.env`의 값으로 덮어쓰지 않습니다.
이전 장에서 같은 이름의 값을 터미널에 설정해 두었다면, `.env`에 Chapter 11 주소를 적어도
다른 프로젝트에 접속할 수 있습니다. 이 명령은 **현재 터미널의 `DATABASE_URL`만 해제**해
항상 `.env`를 쓰게 합니다. 사용자·시스템 전역 설정은 바꾸지 않으며, 새 터미널을 열면 다시 실행합니다.
macOS·Linux에서는 같은 목적으로 `unset DATABASE_URL`을 실행하고, 아래 Python 코드를
`./venv/bin/python`으로 실행합니다.

```powershell
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
@'
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

try:
    load_dotenv(dotenv_path=".env")
    engine = create_engine(os.environ["DATABASE_URL"], hide_parameters=True,
                           connect_args={"connect_timeout": 10})
    with engine.connect() as connection:
        print(connection.execute(text("SELECT 1")).scalar_one())
    engine.dispose()
except Exception as error:
    print("연결 확인 실패:", type(error).__name__)
    raise SystemExit(1)
'@ | & .\venv\Scripts\python.exe -
```

`1`이 출력되면 연결 성공입니다. 오류가 나면 `.env`의 `DATABASE_URL`이 비어 있지 않은지,
Supabase 대시보드의 연결 화면에서 복사한 값과 같은지, 프로젝트가 일시 중지되지 않았는지
([Supabase 대시보드](https://supabase.com/dashboard)) 순서로 확인합니다. 위 코드는 실패 시 오류 종류만
표시합니다. 드라이버 모듈 오류는 URL의 `+psycopg2`와 가상환경 설치를, `OperationalError`는
선택한 연결 방식의 호스트·사용자명·포트와 네트워크 상태부터 확인합니다. 이 이름만으로 세부 원인을
단정하지 말고 연결 확인이 성공한 뒤 다음으로 진행하세요. 연결값이나 오류 원문을 채팅에 붙이지 않습니다.

#### 6단계. 실습 동작 최종 체크리스트

- [ ] `npm ci`와 가상환경의 `pip install`이 성공했다.
- [ ] 3단계에서 백엔드 `venv`의 Python 실행 경로를 확인했고, `.env`에 자신의 연결값을 입력했다.
- [ ] 전용 실습 DB에서 표식 SQL을 실행했다.
- [ ] 5단계의 연결 확인에서 `1`이 출력됐다.
- [ ] 두 서버의 포트 `8000`·`5173`을 사용할 수 있고 Supabase 프로젝트가 활성 상태다.

**환경 준비 완료:** 위 항목을 모두 확인했다면 11.1로 넘어갑니다. 이 장에서 설치와 연결 설정이
가장 번거로운 구간이 끝났습니다. 지금부터는 SQL 실행, Swagger 요청, 브라우저 화면처럼 결과가 눈에 바로 보이는
실습입니다. 연결 확인의 `1`은 DB와 통신했다는 뜻입니다.
주문 테이블·승인 함수는 아직 없는 것이 정상이며, 11.2에서 만들어 첫 승인 결과를 확인합니다.

### [실습 공통] 테스트 데이터 초기화 SQL <a id="reset-sql"></a>

STEP 1에서 테이블과 고정 주문을 만든 뒤 사용합니다. 각 실험에서 초기화를 안내하면
Chapter 11 전용 DB인지 확인하고 아래 SQL 전체를 실행합니다. 테이블·함수는 유지하며
고정 주문 상태·상품 재고·해당 상품의 원장만 복원합니다.

> [!IMPORTANT]
> **[Supabase SQL Editor에서 실행]**
> ```sql
> BEGIN;
> -- 주문 상태 복원 (CREATED) + 재고 복원 (10개) + 원장 초기화
> UPDATE orders SET status = 'CREATED'
>   WHERE order_id = '00000000-0000-0000-0000-000000000001';
> UPDATE stock SET quantity = 10 WHERE product_id = 'PROD-100';
> DELETE FROM stock_ledger WHERE product_id = 'PROD-100';
> COMMIT;
> ```

<a id="ch11-state-query"></a>

**상태 조회:** 아래 SQL로 주문 상태·재고·원장 건수를 요청 전후에 비교합니다.
초기화 직후에는 `CREATED·10·0`인 한 행이어야 합니다. 행이 없으면 STEP 1의 고정 주문·상품 등록을 확인합니다.

```sql
SELECT o.status AS order_status, s.quantity AS current_stock,
       (SELECT COUNT(*) FROM stock_ledger
        WHERE product_id = 'PROD-100') AS ledger_count
FROM orders o
JOIN stock s ON s.product_id = o.product_id
WHERE o.order_id = '00000000-0000-0000-0000-000000000001';
```

**DB 복원과 화면 새로고침은 별도입니다.** 새 실험은 DB 복원 결과를 확인하고 페이지를 새로고침해
시작합니다. 단, **오류 후 같은 화면에서 재시도할 때는 DB만 복원하고 새로고침하지 않습니다.**
화면의 완료 표시가 사라졌다고 DB까지 초기화된 것은 아닙니다.

---

## 11.1 전체 그림 먼저: 우리가 만들 것

Supabase는 클라우드 PostgreSQL과 관리 화면을 제공합니다. 이 장에서는 로컬 DB 설치 대신
Supabase를 사용해 주문·재고·원장을 함께 저장하고, 그 결과를 API와 화면으로 연결합니다.

```mermaid
flowchart TD
    UI["Vue 화면<br/>승인 요청·로딩·결과 표시"]
    API["FastAPI<br/>입력 검사·DB 호출·응답"]
    DB["PostgreSQL 함수<br/>주문·재고 검사와 잠금<br/>재고·원장·주문 변경"]
    UI -->|"POST /orders/approve"| API
    API -->|"approve_order 호출"| DB
    DB -->|"함수 결과 또는 예외"| API
    API -->|"커밋 후 성공<br/>롤백 후 오류"| UI
```

요청과 응답의 순서를 확인하세요.

```mermaid
sequenceDiagram
    participant U as 사용자
    participant V as Vue 화면
    participant A as FastAPI
    participant D as PostgreSQL
    U->>V: 승인 버튼 클릭
    V->>V: 요청 중 잠금·이전 오류 해제
    V->>A: POST /orders/approve
    alt 입력 형식·값 오류
        A-->>V: 422와 필드 오류
    else 입력 검사 통과
        A->>D: approve_order 호출
        D->>D: 주문·재고 검사와 행 잠금
        alt 업무 조건 충족
            D->>D: 재고 차감·원장 기록·주문 PAID 변경
            D-->>A: 함수 반환
            A->>D: commit
            D-->>A: 확정 완료
            A-->>V: 200과 status=success
            V->>V: 완료 표시·성공 후 잠금 유지
        else DB 호출 중 예외
            D-->>A: 예외
            A->>D: rollback
            A-->>V: 400과 detail
        end
    end
    V->>V: finally에서 로딩 해제
```

입력 오류와 DB 오류에서는 완료 상태로 바꾸지 않습니다. 성공 후에는 로딩만 해제되고 완료 상태의 잠금은 유지됩니다.
커밋 중 예외도 API의 롤백·오류 응답 경로로 처리합니다. 이 그림은 코드 흐름입니다.

API 단계부터 백엔드 서버를, 화면 단계부터 프론트엔드 서버도 실행합니다.
터미널 명령은 각 절에 표시된 실행 폴더에서 입력합니다.

```mermaid
flowchart TD
    BT["백엔드 터미널<br/>erp-project"]
    FT["프론트엔드 터미널<br/>frontend-project"]
    API["FastAPI: http://localhost:8000<br/>Swagger: /docs"]
    PAGE["브라우저: http://localhost:5173"]
    DB["Chapter 11 전용<br/>Supabase PostgreSQL"]
    BT -->|"API 서버 실행"| API
    FT -->|"Vite 실행·화면 제공"| PAGE
    PAGE -->|"승인 POST 요청"| API
    API -->|"SQLAlchemy·psycopg2로 DB 함수 호출"| DB
```

<a id="ch11-business-conditions"></a>

**[짧은 실습] 업무 요청에서 빠진 조건 찾기**

업무 담당자가 다음과 같이 요청했다고 생각해 보세요. 아래 문장은 읽기용이며, 그대로 AI에게 구현을 맡기지 않습니다.

> 주문 승인 버튼을 누르면 재고를 차감하고 완료 표시를 해 주세요.

이 요청만으로는 잘못된 주문을 처리하거나 일부 데이터만 저장해도 되는지 알 수 없습니다.
AI에게 묻기 전에 다음 세 질문에 자기 말로 답해 보세요. 파일명이나 SQL 문법은 쓰지 않아도 됩니다.

| 빠진 결정 | 독자가 정할 조건 |
| :--- | :--- |
| 어떤 요청을 거절해야 할까요? | 수량이 잘못됐거나 저장된 주문과 다르거나 재고가 부족할 때의 처리 |
| 무엇을 함께 저장해야 할까요? | 재고만 바뀌고 주문 상태나 원장 기록이 빠져도 되는지 |
| 언제 완료라고 표시해야 할까요? | 버튼 클릭·DB 함수 반환·저장 확정과 성공 응답 중 완료로 판단할 시점 |

생각한 조건은 [관찰 기록](#ch11-manual-record) 아래에 **내가 정한 승인 조건**으로 세 줄만 적습니다.
아직 실행한 결과가 아니므로 `Pass`로 표시하지 않습니다. 뒤의 생성 프롬프트와 비교해 빠진 조건을 보완하고,
11.6에서 실제 코드·실행 결과와 대조합니다. 인증·회사 격리·중복 승인 방지도 실무에서 정해야 할 조건이지만,
이 장에서는 미구현 범위를 식별하는 데 그칩니다. 새 기능을 추가하지 않습니다.

**AI와 작업하는 순서**

`practice-workspace/ch11/`을 연 저장소 접근형 AI를 사용합니다. SQL 생성부터 최종 검토까지 같은
대화를 유지하면 편리하지만, 새 대화에서도 보존한 SQL 실행본과 관찰 기록으로 이어갈 수 있습니다.
관련 파일 전문을 직접 찾아 붙여 넣을 필요는 없습니다.

1. 각 STEP의 프롬프트로 `AGENTS.md`·시작 파일·연결 명세·변경 범위를 조사하게 합니다.
2. API·화면의 조사 결과를 아래 예상 위치와 비교하고, 각 절의 적용 요청을 보냅니다. 범위 밖 변경은 적용 전에 이유를 확인합니다.
3. 핵심 확인 질문으로 생성물을 판정하고 직접 실행합니다. 조건이 같다면 변수명·문법·CSS 차이 때문에 전체 코드를 교체하지 않습니다.
4. 실행 결과는 11.6의 관찰 기록에 남깁니다. 실패하면 원인과 최소 수정 범위를 조사하고, 참조 코드로 복구했다면 사용한 코드와 이유도 적습니다.
5. 마지막에 AI 검토 결과를 실제 코드·SQL·관찰값과 대조한 뒤 11.8의 자가 체크를 완료합니다.

각 실험의 **실행 전 예측** 질문에는 AI에게 묻기 전에 자기 말로 짧게 답해 보세요. 별도 답안은 만들지 않습니다.
예상과 실제 결과가 다르면 코드에서 이유를 찾고, 관찰 기록에는 실제 결과와 차이가 난 이유를 남깁니다.

| 역할 | AI가 확인할 예상 위치 | 확인 기준 |
| :--- | :--- | :--- |
| 작업 규칙 | `AGENTS.md`, `workspace/`와 두 프로젝트의 `AGENTS.md` | 실습 경계와 비밀정보 보호 |
| DB 정의 | STEP 1의 생성 SQL, 실행 후 보존한 `workspace/erp-project/sql/`의 SQL 실행본 | 연결 명세에 맞게 생성하고 실제 실행한 정의를 보존 |
| API | `workspace/erp-project/api/main.py` | 요청 검사·DB 호출·커밋·롤백 |
| 화면 | `workspace/frontend-project/src/components/ApproveOrder.vue`, `src/App.vue` | 컴포넌트 생성·앱 등록·요청과 화면 상태 처리 |
| 실행 환경 | 두 프로젝트의 의존성 파일, 프론트엔드 `src/main.js` | 기존 설정·의존성 유지 |
| 자동 검증 | Chapter 11 폴더에서 조사 | 없으면 `테스트 없음`, 미실행은 `Not Run` |

diff는 변경 전후의 차이를 보여 주는 비교 결과입니다. Git을 쓰지 않는 폴더에서는 변경 전후 비교를 요청합니다.
참조 코드는 비교·복구용입니다.
심화 질문에서도 `.env`·비밀값 읽기와 DB 접속은 AI에 허용하지 않으며, SQL 실행은 독자가 직접 합니다.

---

## 11.2 STEP 1: 주문·재고·원장을 함께 저장하기 (Supabase SQL Editor)

> **[반드시 따라하기]** 테이블·함수를 만들고 정상 승인 결과를 확인합니다.

### 무엇을 하는가

주문 승인에 필요한 주문·재고·원장 테이블과 DB 함수를 만듭니다. **원자성**은 함께 바뀌어야 할
데이터를 일부만 저장하지 않는 성질입니다. **트랜잭션**은 여러 쓰기를 한 묶음으로 처리해
모두 확정(commit)하거나 모두 취소(rollback)하는 단위입니다. DB 함수의 쓰기를 하나의 트랜잭션으로 묶되,
인증·회사 접근 통제·중복 승인 방지는 아직 구현하지 않습니다.

### 코드 / 명령어

**AI 조사·생성:** 다음 프롬프트를 같은 AI 대화에서 실행합니다. 테이블·함수 이름은
후속 API와 초기화 도구를 연결하기 위한 실습 명세입니다.

**프롬프트를 읽는 기준:** [11.1에서 정한 조건](#ch11-business-conditions) 중 거절할 요청과 함께 저장할 데이터를
찾아보세요. 재고에서 3개를 빼면 원장에도 `-3`을 기록하고 주문을 승인 완료로 바꾸며, 세 변경은 전부 저장되거나 전부 취소되어야 합니다.

아래의 DDL은 테이블 구조를 만드는 SQL입니다. PK는 행을 구별하는 기본 키, FK는 다른 테이블의
행을 참조하는 외래 키이며, UUID는 주문 ID에 쓰는 식별자 형식입니다. 이름과 타입은 뒤의 코드가
같은 데이터를 찾기 위한 약속이므로 그대로 제공합니다.
`FOR UPDATE`는 처리 중인 행을 다른 요청이 동시에 바꾸지 못하게 잠그는 구문입니다.
함수가 끝나도 잠금이 바로 풀리는 것은 아니며, 호출한 트랜잭션이 확정·취소될 때까지 유지됩니다.
11.2에서는 SQL Editor에서 실행하고, 11.3부터는 API가 함수를 호출한 뒤 확정·취소합니다.

> **[AI 프롬프트: 테이블 DDL 및 원자성 함수 생성]**
>
> ```text
> Chapter 11 폴더를 열었습니다. AGENTS.md와 저장소에서 DB 준비·초기화 도구와 시작 파일을 조사하세요.
> 파일 수정·DB 접속·.env와 비밀값 읽기 및 출력은 하지 마세요.
> 현재 제공된 SQL과 없는 정의를 구분해 보고하고, 다음 연결 명세와 업무 조건에 맞는 PostgreSQL(Supabase) SQL을 답변으로 작성하세요.
> 아래 테이블·함수 이름은 이후 API와 초기화 도구가 사용하는 실습 명세입니다.
> 
> 1. 핵심 테이블 생성:
>    - stock:
>      * product_id (PK, 문자열)
>      * quantity (정수, 0 이상 제약조건)
>      * corp_id (회사 소속 식별 필드, 문자열, 기본값 'HQ'; 접근 통제는 별도)
>    - orders:
>      * order_id (PK, UUID)
>      * product_id (FK)
>      * quantity (정수, 1 이상 제약조건)
>      * status (문자열, 'CREATED', 'PAID' 중 하나)
>      * created_at (타임스탬프)
>      * corp_id (회사 소속 식별 필드, 문자열, 기본값 'HQ'; 접근 통제는 별도)
>    - stock_ledger:
>      * ledger_id (PK, 자동증가)
>      * product_id (FK)
>      * qty_change (정수)
>      * reason (문자열)
>      * created_at (타임스탬프)
>      * corp_id (회사 소속 식별 필드, 문자열, 기본값 'HQ'; 접근 통제는 별도)
>    - 현재고(stock.quantity)·주문 수량(orders.quantity)·주문 상태(orders.status)·원장 증감량(stock_ledger.qty_change)은 NULL로 저장할 수 없어야 함.
>    - 세 테이블의 corp_id도 NULL을 허용하지 않으며, 값을 생략하면 기본값 'HQ'를 사용.
> 
> 2. 주문 승인(approve_order) DB 함수 작성:
>    - 호출 형식은 approve_order(UUID, VARCHAR, INTEGER). 주문 ID, 상품 ID, 수량을 받음.
>    - 수량이 NULL 또는 0 이하이거나, 주문이 없거나, 요청 상품·수량이 저장된 주문과 다르면 쓰기 전에 거절.
>    - 검사한 주문이 처리 도중 바뀌지 않도록 해당 주문 행을 잠금.
>    - stock 테이블에서 product_id의 행을 FOR UPDATE로 비관적 락을 걸고 현재 재고 확인.
>    - 재고가 부족하면 쓰기 전에 예외로 거절.
>    - 재고가 충분하면:
>      * stock의 quantity 차감
>      * stock_ledger에 qty_change를 음수로 기록
>      * orders의 status를 'PAID'로 변경.
>    - 이번 실습에는 인증·회사 접근 통제·중복 승인 방지를 추가하지 않음.
>      같은 주문을 재요청하면 재고가 충분한 동안 다시 차감될 수 있음을 보고.
>    - 함수 내부에서 커밋하지 않으며, 호출자가 한 트랜잭션으로 확정·취소할 수 있어야 함.
>
> 입력 거절 위치·첫 쓰기·잠금 범위·호출자에게 맡긴 처리를 설명하세요.
> 기존 데이터를 삭제하는 SQL과 샘플·시드 데이터 INSERT는 추가하지 말고, 아직 실행하지 않은 결과를 성공으로 보고하지 마세요.
> ```

NULL은 값이 없음을 나타냅니다. `CHECK`로 수량 범위나 상태값을 제한해도 NULL까지 막지는 못하므로,
위 필수 값에는 `NOT NULL`도 있는지 생성 SQL에서 확인하세요.

**핵심 패턴 확인:** 생성 SQL에서 다음 세 곳을 찾습니다. 문법이 달라도 같은 조건을 만족하면 유지합니다.

| 확인할 위치 | 판단 기준 |
| :--- | :--- |
| 첫 쓰기 전 검사 | 양수 수량·주문 존재·상품/수량 일치·재고 충분 여부를 확인 |
| 주문·재고의 `FOR UPDATE` | 같은 행을 바꾸는 요청을 기다리게 하는 잠금. 접근 권한·재승인 검사는 별도 |
| 재고 차감·원장·주문 변경 | 세 쓰기 사이에 커밋이 없으며 호출자가 함께 확정·취소 |

검사와 쓰기 위치를 찾기 어렵다면 AI에게 “위 세 기준에 해당하는 생성 SQL의 위치와 이유를 짚어 주세요.
SQL 수정·실행은 하지 마세요”라고 요청하고, 답변이 가리킨 조건문·잠금·세 변경을 직접 확인하세요.
이 확인은 코드 검토입니다. 실제 저장 결과는 아래 정상 승인 실행과 상태 조회로 따로 확인합니다.

참조 함수의 재고 검사 부분입니다. 생성물에서도 같은 역할을 찾아보세요.

```sql
SELECT quantity INTO v_current_stock
FROM stock
WHERE product_id = p_product_id
FOR UPDATE;

IF v_current_stock < p_qty THEN
    RAISE EXCEPTION '재고가 부족합니다. (현재 재고: %, 요청 수량: %)',
        v_current_stock, p_qty;
END IF;
```

### 확인 방법

**실행 위치: Chapter 11 전용 Supabase SQL Editor.** 테이블·함수 생성과 고정 데이터 등록을 마친 뒤
`CREATED·10·0 → PAID·7·1`을 확인하고, 마지막에 `CREATED·10·0`으로 복원합니다.

1. Supabase에서 **Chapter 11 전용 프로젝트 → SQL Editor → 새 쿼리**를 엽니다.
   조건을 만족한 생성 SQL을 한 번 실행합니다. 성공했다면 아래 [SQL 실행본 보존 절차](#ch11-sql-record)에
   따라 실행한 내용을 파일로 남깁니다. [전체 참조 SQL](#ch11-db-reference)은 비교·복구용이며 생성 SQL과 둘 다 실행하지 않습니다.
2. 테이블·함수가 만들어졌다면 아래 SQL로 고정 상품·주문을 등록합니다. 최초 한 번만 실행합니다.

   ```sql
   INSERT INTO stock (product_id, quantity) VALUES ('PROD-100', 10);
   INSERT INTO orders (order_id, product_id, quantity, status)
   VALUES ('00000000-0000-0000-0000-000000000001', 'PROD-100', 3, 'CREATED');
   ```

3. [상태 조회](#ch11-state-query)에서 `CREATED·10·0`을 확인합니다.
   **실행 전 예측:** 3개를 승인하면 재고 수량과 원장의 증감량은 각각 얼마가 되고, 주문 상태는 어떻게 바뀔까요?
   예상한 뒤 다음 함수를 한 번 호출합니다.

   ```sql
   SELECT approve_order('00000000-0000-0000-0000-000000000001', 'PROD-100', 3);
   ```

4. 같은 상태 조회에서 `PAID·7·1`을 확인합니다. 원장의 차감 수량도 아래 조회로 확인합니다.

   ```sql
   SELECT qty_change FROM stock_ledger WHERE product_id = 'PROD-100';
   ```

   한 행에 `-3`이면 재고 3개 차감과 원장 기록이 일치합니다. 이는 정상 저장 관찰입니다.
   실패 경로는 11.6에서 확인합니다.
5. [초기화 SQL](#reset-sql)을 실행하고 상태 조회가 `CREATED·10·0`으로 돌아왔는지 확인합니다.

**다음 단계 조건:** 정상 승인 결과와 시작 상태 복원을 확인했다면 11.3으로 넘어갑니다.
고정 주문 UUID·상품·수량은 뒤의 API와 화면에서도 그대로 사용합니다.

<a id="ch11-sql-record"></a>

**SQL 실행본 보존하기**

AI 답변과 SQL Editor에서 실제 실행한 내용이 다를 수 있습니다. 나중에 같은 정의를 검토할 수 있도록,
1번에서 성공한 테이블·함수 생성 SQL을 SQL Editor에서 복사해 직접 파일로 저장합니다.
SQL Editor의 내용을 복사해 파일 하나로 저장합니다. 이후 API 연결과 AI 검토가 이 파일을 근거로
삼으므로 건너뛰지 않습니다.

1. VS Code에서 `ch11/` 기준 `workspace/erp-project/sql/` 폴더를 만들고,
   `01_approve_order.executed.sql` 파일에 실행한 SQL을 저장합니다. 이 폴더는 백엔드의 수정 허용 범위 안에 있으며,
   키트가 미리 제공하는 폴더가 아닙니다. 고정 데이터 INSERT·승인 호출·초기화 SQL은 이 파일에 섞지 않습니다.
2. 실행하지 않은 AI 제안이나 실패한 SQL을 실행본으로 저장하지 않습니다. 연결 문자열·비밀번호·대시보드 화면도 넣지 않습니다.
3. 이후 함수를 수정해 성공적으로 실행했다면 이전 파일을 보존하고 `02_approve_order.executed.sql`처럼
   번호를 늘려 해당 변경 SQL을 저장합니다. 검토할 때는 번호순으로 읽고 마지막으로 적용한 정의를 확인합니다.
4. `observation_record.md`에 실행본의 상대 경로·실행 순서·성공 여부를 직접 기록합니다.
   참조 SQL로 복구했다면 실제 실행한 내용을 같은 방식으로 보존하고 복구 이유도 기록합니다.

이 파일은 검토를 위한 실행 기록입니다. 새 AI 대화에서는 `AGENTS.md`·SQL 실행본·관찰 기록을 읽고
마지막 완료 단계와 다음 실험을 확인하게 하세요. 파일을 읽었다는 이유로 SQL을 다시 실행하지 않습니다.
DB에서 별도로 정의를 바꿨거나 실행본이 없다면 현재 DB 정의와 일치하는지는 미확인으로 남깁니다.

> **[막혔을 때]** 외래 키는 다른 테이블의 값을 참조하는 연결입니다. 참조 오류가 나면
> 부모인 `stock`이 먼저 생성됐는지 확인하세요. 고정 데이터 등록에서 중복 키 오류가 나면 같은 ID의 데이터가 이미 있는지,
> 생성 SQL에 샘플 INSERT가 포함됐거나 등록 명령을 다시 실행했는지 확인합니다. 이미 만든 테이블이나 고정 데이터를 다시 등록하지 말고,
> 현재 상태와 실패 위치부터 조사합니다. 복구가 필요하면 [참조 SQL](#ch11-db-reference)과 비교합니다.

---

## 11.3 STEP 2: DB 함수를 호출하는 API 만들기 (FastAPI)

> **[반드시 따라하기]** DB 함수를 호출하는 API를 만들고 Swagger에서 확인합니다.

### 무엇을 하는가

API는 요청 형식·양수 수량을 검사하고, 주문 일치·재고 판단과 저장은 DB 함수에 맡깁니다.
호출 결과를 응답으로 바꾸는 데 집중하는 구조를 **Thin Layer API(처리 책임을 좁힌 API)**라고 부릅니다.

이 장의 SQLAlchemy·psycopg2 호출은 DB 응답을 기다리는 동안 실행을 멈추는 동기 방식입니다.
따라서 경로 함수를 일반 `def`로 작성해 FastAPI가 작업 스레드에서 실행하게 합니다.
`async def`라는 선언만으로 동기 DB 호출이 비동기로 바뀌지는 않습니다.

이 API는 `http://localhost:5173`에서 열린 화면의 호출을 받아야 합니다. 화면과 API는 포트가 달라
서로 다른 출처입니다. 브라우저는 기본적으로 다른 출처의 응답을 JavaScript가 읽는 것을 제한합니다.
서버가 허용할 출처·요청 방식을 응답 헤더로 알려 주는 규칙이 **CORS**입니다.
이 장의 JSON POST에서는 브라우저가 먼저 `OPTIONS` 요청으로 허용 여부를 확인하고, 허용되면 실제 요청을 보냅니다.
Swagger는 API와 같은 출처(`http://localhost:8000`)에서 열리지만, 11.4의 Vue 화면에는 CORS 설정이 필요합니다.

### 프로젝트 디렉터리 구조

`workspace/erp-project/`의 기존 의존성을 사용해 `api/main.py`를 생성합니다.
`api/__init__.py`와 `requirements.txt`는 시작 키트에 있습니다. 별도 프로젝트를 만들거나
프론트엔드 파일·DB 정의를 변경하지 않습니다.

### 코드 / 명령어

**AI 조사·생성:** 먼저 다음 프롬프트로 API 연결에 필요한 근거와 변경 범위를 조사합니다.

> **[AI 프롬프트: FastAPI Thin Layer API 작성]**
>
> ```text
> Chapter 11의 AGENTS.md와 백엔드 시작 파일·의존성·테스트 유무를 조사하세요.
> 보존한 SQL 실행본과 관찰 기록에서 주문 승인 DB 함수를 확인하고, API를 연결할 위치·변경 범위·이유를 보고하세요. 아직 수정하지 마세요.
> 실행본이나 실행 여부가 미확인이면 연결을 추측하지 말고 누락된 근거를 알려 주세요.
> DB 접속과 .env·연결 문자열·비밀값 읽기 및 출력은 하지 마세요.
>
> [완성할 동작]
> - FastAPI + SQLAlchemy로 POST /orders/approve를 제공합니다.
> - 본문은 order_id(UUID), product_id(문자열), qty(1 이상 정수)입니다.
> - 수량 0·음수·잘못된 UUID는 DB 호출 전 422로 거절합니다.
> - 업무 처리는 approve_order DB 함수에 맡기고, 성공 시 커밋한 뒤 HTTP 200과 {"status":"success"}를 반환합니다.
> - 함수 호출·커밋 중 예외는 롤백하고, 학습용 응답 400의 detail로 원인을 전달합니다.
> - http://localhost:5173의 Vue 화면에서 호출할 수 있어야 합니다.
>
> [변경 경계와 완료 보고]
> 현재 작업 규칙의 단일 API 파일 구조를 유지하며, DB 정의·의존성·프론트엔드는 바꾸지 않습니다.
> 런타임은 백엔드 로컬 .env의 DATABASE_URL을 사용하며 실제 값을 코드에 넣지 않습니다.
> 의존성의 psycopg2 드라이버와 연결하고, 기존 프로세스 값은 실행 터미널에서 정리하는 원고 절차를 따릅니다.
> 동기 SQLAlchemy·psycopg2 호출에 맞게 경로 함수를 일반 def로 작성해 DB 대기가 이벤트 루프를 막지 않게 합니다.
> 인증·중복 승인 방지·다른 업무 API는 추가하지 않습니다. 범위 밖 변경은 적용 전에 이유를 보고하세요.
> 적용 뒤 diff·구문 검사·입력 검사 결과와 미검증 범위를 보고하세요. 실제 DB 실행은 독자가 수행합니다.
> ```

조사 결과를 11.1의 예상 위치표와 비교하세요. SQL 실행본 등 필요한 근거가 확인되고 변경 범위가 맞으면,
같은 AI 대화에서 다음 적용 요청을 보냅니다.

```text
앞서 정한 동작·변경 경계·비밀정보 보호 조건을 지키며, 확인한 범위에서 API의 최소 변경을 적용해 주세요.
변경 전후 diff와 구문·입력 검사 결과를 보고하고, 실행하지 못한 검증은 Not Run으로 남겨 주세요.
```

**핵심 패턴 확인:** 생성된 API에서 다음 세 곳을 찾습니다.

| 확인할 위치 | 판단 기준 |
| :--- | :--- |
| 요청 모델 | UUID와 `qty >= 1`을 검사해 잘못된 입력을 DB 호출 전 422로 거절 |
| DB 호출·성공 응답 | 요청값을 SQL 매개변수로 전달하고 커밋이 끝난 뒤 성공 반환 |
| 실패·요청 종료 | 예외 시 롤백 후 오류 응답, `get_db()`의 `finally`에서 세션 닫기 |

참조 API의 호출·확정·취소 부분입니다. `text()`는 SQLAlchemy가 실행할 SQL 객체를 만들고,
`:id` 같은 매개변수에 값을 따로 전달합니다. 요청값을 SQL 문자열에 직접 이어 붙이지 않습니다.

```python
try:
    db.execute(
        text("SELECT approve_order(:id, :pid, :q)"),
        {"id": request.order_id, "pid": request.product_id, "q": request.qty}
    )
    db.commit()
    return {"status": "success"}
except Exception as e:
    db.rollback()
    raise HTTPException(status_code=400, detail=str(e))
```

함수의 `BEGIN~END`는 실행문을 묶는 블록이며 커밋 명령이 아닙니다. 이 API에서는
`db.commit()`·`db.rollback()`이 확정·취소를 담당합니다. 전체 연결 설정과 세션 처리는
[참조 API](#ch11-api-reference)에서 비교할 수 있습니다.

**오류 응답의 학습 범위:** 위 코드는 원인을 관찰하기 쉽게 DB 예외 문자열 전체를 `detail`에 담고,
연결 실패 같은 서버 오류도 `400`으로 반환합니다. 따라서 `400`만 보고 재고 부족이라고 판단하면 안 됩니다.
`detail`에는 SQL·함수 이름 같은 내부 정보가 포함될 수 있습니다. 이 응답은 로컬 실습에서만 관찰하며,
실제 서비스에서는 사용자에게 보여 줄 메시지와 서버 로그를 분리하고 업무 오류와 서버 오류를 구분합니다.
`hide_parameters=True`도 예외 문자열의 모든 내부 정보를 제거하지는 않습니다. 자세한 한계는 11.7에서 확인합니다.

### 확인 방법

**실행 위치: 백엔드 터미널 → Swagger.** DB는 `CREATED·10·0`에서 시작합니다.
성공 응답과 `PAID·7·1`을 확인한 뒤 DB를 복원하고, 백엔드 서버는 켜 둡니다.

1. **백엔드 터미널**에서 기존 `venv`의 Python으로 실행합니다. 현재 폴더는
   `practice-workspace/ch11/workspace/erp-project/`여야 합니다.

   ```powershell
   Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
   & .\venv\Scripts\python.exe -m uvicorn api.main:app --reload
   ```

   첫 명령은 11.0-ENV 5단계에서 설명한 것과 같은 이유로 실행합니다. 새 터미널을 열었다면 다시 적용합니다.
   macOS·Linux에서는 `unset DATABASE_URL`을 실행한 뒤
   `./venv/bin/python -m uvicorn api.main:app --reload`로 서버를 실행합니다.

2. `http://localhost:8000/docs`에서 `POST /orders/approve`를 펼치고 **Try it out**을 누릅니다.
   [상태 조회](#ch11-state-query)로 `CREATED·10·0`인지 확인한 뒤 아래 본문을 입력합니다.

   ```json
   {
     "order_id": "00000000-0000-0000-0000-000000000001",
     "product_id": "PROD-100",
     "qty": 3
   }
   ```

3. **실행 전 예측:** 성공 응답은 DB 함수가 반환한 직후와 커밋이 끝난 뒤 중 언제 보내야 할까요?
   생성한 API에서 순서를 찾은 뒤 **Execute를 한 번만** 누릅니다.
   응답 `200`·`{"status":"success"}`와 DB 상태 `PAID·7·1`을 대조합니다.
   확인을 위해 다시 요청하지 않습니다. 현재 함수에는 중복 승인 방지가 없어 추가 차감될 수 있습니다.
4. [초기화 SQL](#reset-sql)을 실행하고 `CREATED·10·0`으로 복원됐는지 확인합니다.

**다음 단계 조건:** 성공 응답·DB 결과·복원을 확인했다면 서버를 실행한 채 11.4로 넘어갑니다.
수량 0과 잘못된 UUID의 실제 거절 결과는 11.6에서 따로 확인합니다.

> **[막혔을 때]** `No module named 'api'`가 나오면 현재 폴더가 `erp-project/`인지,
> 기존 `venv`의 Python을 사용했는지, `api/main.py`가 있는지(`Test-Path api/main.py`)를 차례로 확인합니다.
> Python 실행 경로 확인은 11.0-ENV 3단계의 안내를 따릅니다. DB 연결이 실패하면
> 자신의 로컬 `DATABASE_URL`과 Supabase 프로젝트 상태를 확인합니다. 이 API는 DB 호출 중 생기는
> 모든 예외를 `400`으로 돌려주므로, 연결 실패도 `400`의 `detail`에 연결 오류로 나타납니다.
> 업무 오류와 구분하려면 11.0-ENV 5단계의 연결 확인부터 다시 실행합니다. 연결값은 AI에 전달하지 않습니다.
> 패키지 설치 오류는 11.0-ENV의 `requirements.txt` 설치 단계로 돌아가 확인하고,
> API 동작 차이는 [참조 API](#ch11-api-reference)와 비교합니다.

---

## 11.4 STEP 3-A: 승인 API를 호출하는 화면 만들기

> **[반드시 따라하기]** 로딩·성공·오류 처리를 포함한 주문 승인 화면을 한 번 생성합니다.

### 무엇을 하는가

고정 주문을 API에 보내고 결과를 화면에 표시합니다. 요청 중 버튼 잠금과 성공·실패 표시까지
함께 만듭니다. 이 절에서는 화면 연결을 준비하고, 11.5에서 한 번의 정상 요청으로 동작을 관찰합니다.

### 코드 / 명령어

**AI 조사·생성:** 먼저 다음 프롬프트로 화면의 변경 범위를 조사합니다.
Vue Options API와 키트에 포함된 Axios(브라우저에서 API를 호출하는 라이브러리)를 사용하며 별도 UI 라이브러리는 설치하지 않습니다.

> **[AI 프롬프트: 주문 승인 화면과 상태 처리 구현]**
>
> ```text
> Chapter 11의 AGENTS.md와 프론트엔드 시작 화면·앱 등록 위치·의존성을 조사하세요.
> 이번 단계에서 만들거나 바꿀 파일과 이유를 보고하고, 아직 수정하지 마세요.
> DB 접속과 .env·비밀값 읽기 및 출력은 하지 마세요.
>
> [화면에서 완료할 동작]
> - Vue Options API와 기존 Axios로 주문 ID·상품 ID·수량을 보여주는 단일 카드 화면을 만듭니다.
> - 값은 주문 00000000-0000-0000-0000-000000000001, 상품 PROD-100, 수량 3입니다.
> - [주문 승인 API 호출]을 누르면 POST http://localhost:8000/orders/approve로
>   order_id, product_id, qty를 보냅니다.
> - 요청 대기 중에는 '처리 중...'을 표시하고 추가 클릭을 막습니다.
> - 200의 status=success를 확인한 경우에만 화면 안에 완료 메시지와 '승인 완료' 버튼을 표시하고 잠금을 유지합니다.
> - 실패하면 완료 상태로 바꾸지 않고 응답의 detail을 화면 안에 표시하며, 다시 요청할 수 있어야 합니다.
> - 응답이 없는 통신 오류에는 이해할 수 있는 대체 메시지를 표시합니다. 재시도 시 이전 오류를 지웁니다.
> - 앱의 시작 화면에서 이 카드를 볼 수 있도록 연결합니다. 기존 개인 작업은 보존하고 변경을 최소화합니다.
> - 버튼은 키보드로도 사용할 수 있어야 하며, 좁은 화면에서 주문 정보와 결과를 읽을 수 있어야 합니다.
> - 현재 화면의 잠금을 서버의 중복 승인 방지로 설명하지 않습니다.
>
> [변경 경계와 완료 보고]
> API·DB·의존성·다른 화면은 변경하지 말고, 범위 밖 변경은 적용 전에 파일과 이유를 보고하세요.
> 별도 CSS 라이브러리는 설치하지 않습니다. 생성 코드의 변수명과 스타일은 현재 프로젝트에 맞게 정하세요.
> 적용 뒤 변경 파일·diff·빌드 결과와 요청·로딩·성공·오류·재시도 처리 위치를 보고하세요.
> 브라우저에서 직접 확인하지 않은 결과는 Not Run으로 남기세요.
> ```

조사한 변경 파일을 아래 예상 위치표와 비교하세요. 주문 카드와 시작 화면 연결 범위가 맞으면,
같은 AI 대화에서 다음 적용 요청을 보냅니다.

```text
앞서 정한 화면 동작·변경 경계·비밀정보 보호 조건을 지키며, 확인한 범위에서 화면의 최소 변경을 적용해 주세요.
변경 전후 diff와 빌드 결과를 보고하고, 브라우저에서 직접 확인하지 않은 결과는 Not Run으로 남겨 주세요.
```

**예상 위치표:** 빈 파일을 직접 만들 필요는 없습니다. 적용 뒤에는 이 위치에서 생성 결과를 확인합니다.

| 역할 | 예상 위치 | 확인할 것 |
| :--- | :--- | :--- |
| 주문 카드와 요청 처리 | `workspace/frontend-project/src/components/ApproveOrder.vue` | 고정 입력·API 요청·상태 표시 |
| 시작 화면 연결 | `workspace/frontend-project/src/App.vue` | 컴포넌트 import와 등록·화면 배치 |

개인 작업이 있다면 diff를 확인합니다. 키트의 `workspace/_starter/App.vue`는 시작 화면 복원용이며
개인 작업의 백업은 아닙니다. 앱 연결과 상태 처리의 [전체 참조 코드](#ch11-ui-state-reference)는
막혔을 때 비교·복구하는 용도입니다.

### 확인 방법

1. 11.3의 백엔드 서버는 실행한 채 둡니다. 프론트엔드 터미널에서 다음 명령을 실행합니다.
   자신의 키트 설치 위치가 다르면 경로를 바꾸세요.

   ```powershell
   Set-Location C:\erp-book\foundation-lab-kit\practice-workspace\ch11\workspace\frontend-project
   npm run dev -- --port 5173 --strictPort
   ```

   이미 5173에서 실행 중이라면 다시 실행하지 않습니다. 포트가 사용 중이면 해당 터미널을 먼저
   확인하세요. `--strictPort`는 다른 포트로 자동 변경되는 것을 막아 API의 허용 주소와 맞춥니다.
2. `http://localhost:5173`에서 주문·상품·수량과 승인 버튼이 보이는지 확인합니다.
   **아직 버튼을 누르지 않습니다.** 요청·로딩·성공 결과는 11.5에서 한 번에 확인합니다.

**다음 단계 조건:** 카드가 시작 화면에 보이면 코드를 교체하지 않고 11.5로 넘어갑니다.
화면이 비어 있다면 브라우저 콘솔과 앱의 컴포넌트 등록부터 확인합니다.

---

## 11.5 STEP 3-B: 요청 중 버튼 잠금과 성공·오류 표시 확인하기

> **[반드시 따라하기]** 11.4에서 만든 화면의 상태와 실제 API·DB 결과를 확인합니다.

### 무엇을 하는가

화면을 다시 생성하지 않습니다. 이미 만든 요청·상태 처리의 역할을 코드에서 찾고
브라우저의 동작과 연결합니다. 변수명이 참조와 달라도 역할이 같으면 유지합니다.

### 코드 / 명령어

| 참조 코드의 상태 | 화면에서 확인할 행동 |
| :--- | :--- |
| `isLoading` | 요청 중 '처리 중...' 표시와 버튼 잠금, 응답 후 로딩 해제 |
| `isPaid` | 성공 응답 뒤에만 완료 표시, 로딩이 끝나도 버튼 잠금 유지 |
| `errorMessage` | 실패 원인 표시, 다음 요청 시작 시 이전 오류 해제 |

```mermaid
flowchart TD
    START["클릭: isLoading=true<br/>이전 errorMessage 지우기"] --> REQUEST["승인 API 요청"]
    REQUEST --> OK{"HTTP 200이고<br/>status=success인가?"}
    OK -->|"예"| SUCCESS["isPaid=true<br/>완료 메시지 표시"]
    OK -->|"그 밖의 응답"| UNEXPECTED["완료 응답 미확인<br/>오류 표시"]
    REQUEST -->|"요청 실패"| ERROR["detail 또는<br/>통신 오류 메시지 표시"]
    SUCCESS --> FINAL["finally: isLoading=false"]
    UNEXPECTED --> FINAL
    ERROR --> FINAL
    FINAL --> LOCK{"isPaid인가?"}
    LOCK -->|"예"| PAID["승인 완료: 버튼 잠금 유지"]
    LOCK -->|"아니요"| RETRY["실패: 다시 요청할 수 있음"]
```

참조 코드에서는 버튼에 다음 조건을 연결합니다. 성공 후에는 `isLoading`이 꺼져도 `isPaid`로 잠금을 유지합니다.

```html
:disabled="isLoading || isPaid"
```

이 잠금은 현재 화면의 추가 클릭을 막는 장치입니다. 새로고침이나 다른 클라이언트의 요청까지
막지는 않으며, 서버의 중복 승인 방지는 이번 실습에 구현되어 있지 않습니다.

### 확인 방법

**실행 위치: Vue 화면과 개발자 도구 Network.** 두 서버를 켠 상태에서 DB는 `CREATED·10·0`,
화면은 새로고침한 상태로 시작합니다. 성공 응답·완료 표시·DB `PAID·7·1`을 함께 확인합니다.

**실행 전 예측:** 성공 후 로딩이 끝나도 버튼을 잠가 두려면 어떤 상태가 남아 있어야 할까요?

1. [상태 조회](#ch11-state-query)로 `CREATED·10·0`을 확인합니다. 다르면 [초기화 SQL](#reset-sql)을
   실행합니다. Vue 페이지를 새로고침해 화면도 시작 상태로 돌립니다.
2. 개발자 도구의 **Network** 기록을 비우고 네트워크 속도를 `Slow 3G`로 설정합니다.
   [주문 승인 API 호출]을 한 번 누르고 대기 중 버튼이 '처리 중...'으로 잠기는지 확인합니다.
3. 대기 중 추가 클릭을 시도해도 승인 POST가 한 건인지 확인합니다. `OPTIONS`는 세지 않습니다.
   요청 주소는 `http://localhost:8000/orders/approve`, 본문은 고정 주문 UUID·`PROD-100`·`qty: 3`이어야 합니다.
4. 같은 요청의 응답 `200`·`status=success`, 화면의 완료 메시지·버튼 잠금 유지,
   DB 상태 `PAID·7·1`을 대조합니다. 버튼 색상이나 CSS 값까지 참조와 같을 필요는 없습니다.
   성공했을 때 화면은 다음과 같이 보입니다. 디자인이 달라도 완료 메시지와 잠긴 버튼이 있으면 됩니다.

   ![승인 성공 후 완료 메시지와 잠긴 승인 완료 버튼이 표시된 화면](images2/11_chapter11_approve_success.png)
5. 네트워크 속도를 `No throttling`으로 되돌리고 이 결과를 [11.6 관찰 기록](#ch11-manual-record)의
   정상 승인 행에 남깁니다. 확인하려고 새 성공 요청을 보내지 않습니다.

**다음 단계 조건:** 정상 승인·로딩 잠금·DB 결과를 확인했다면 11.6으로 넘어갑니다.
재고 부족 오류와 같은 화면에서 재시도는 그 절차에 따라 검증합니다.

> **[막혔을 때]**
>
> - 화면의 요청 오류는 Network에서 실제 주소·본문·응답부터 확인합니다. CORS 오류는 현재 페이지가
>   API에서 허용한 `http://localhost:5173`인지, 404는 요청 주소가 맞는지, 422는 오류 필드가 무엇인지 확인합니다.
> - 로딩이 멈췄다면 요청이 아직 `Pending`인지 먼저 봅니다. 참조 코드에는 요청 제한 시간이 없어 응답 전에는
>   `finally`에 도달하지 않습니다. 결과를 모르는 요청은 반복 전송하지 말고 DB 상태부터 조회합니다.
> - 응답이 끝났는데 상태가 다르면 생성 코드의 로딩 해제·성공 판정·오류 표시를 [참조 코드](#ch11-ui-state-reference)와
>   비교합니다. 전체 파일을 바꾸기 전에 최소 수정 범위를 확인하고, 바꾼 코드로 관련 실험을 다시 수행합니다.

---

## 11.6 검증: 내가 만든 것이 제대로 동작하는가

> **[반드시 따라하기]** 관찰 기록표 하나에 실행 결과를 모으고 AI 검토 뒤 직접 대조합니다.

### 1차 검증: 수동 테스트 시나리오

각 요청 직전·직후에 [상태 조회](#ch11-state-query)로 주문 상태·재고·원장 건수를 기록합니다.
아래 값은 예상값이며, 실제 응답·화면·DB 값을 [관찰 기록표](#ch11-manual-record)에 남깁니다.

**실험 순서와 시작 상태:** 요청은 실행 위치 열의 화면에서 보내고, DB 상태는 SQL Editor에서 조회합니다.
처음에는 두 서버가 켜져 있어야 합니다. 마지막 통신 오류 실험에서만 API를 종료합니다.
`CREATED·10·0`은 **주문 상태·재고·원장 건수** 순서입니다.

| 실험 | 실행 위치 | 요청 전 DB | 화면 준비 | 확인할 결과 |
| :--- | :--- | :--- | :--- | :--- |
| 정상 승인 | 11.5의 결과 사용 | `CREATED·10·0` | 11.5에서 확인함 | 200·완료 표시·`PAID·7·1` |
| 재고 부족 | Vue 화면 | 초기화 후 재고를 줄여 `CREATED·2·0` | 새로고침 | 400·재고 부족 표시·DB 불변 |
| 같은 화면에서 재시도 | Vue 화면 | DB만 복원해 `CREATED·10·0` | 오류 화면 유지, 새로고침하지 않음 | 200·이전 오류 해제·`PAID·7·1` |
| 수량 0 | Swagger | `PAID·7·1` | Vue 화면 조작 없음 | 422·qty 오류·DB 불변 |
| 잘못된 UUID | Swagger | `PAID·7·1` | Vue 화면 조작 없음 | 422·order_id 오류·DB 불변 |
| 통신 오류 | API 종료 후 Vue 화면 | `PAID·7·1` | 새로고침 | HTTP 응답 없음·대체 오류 표시·DB 불변 |

1. **정상 승인:** 11.5의 결과를 그대로 기록합니다. 아직 실행 전이라면 그 절로 돌아가 진행하세요.
2. **재고 부족:** [초기화 SQL](#reset-sql)로 DB를 되돌리고 페이지를 새로고침합니다.
   이어서 전용 DB에서 아래 SQL로 재고를 2개로 줄이고 `CREATED·2·0`을 확인합니다.

   ```sql
   UPDATE stock SET quantity = 2 WHERE product_id = 'PROD-100'
   RETURNING product_id, quantity;
   ```

   **실행 전 예측:** 재고 2개에서 3개를 승인하려 하면 첫 쓰기 전에 거절될까요? 주문·재고·원장 중 바뀌는 값이 있을까요?
   키보드로 실행합니다. `Tab`으로 승인 버튼에 이동해 포커스 표시가 보이는지 확인하고,
   `Enter` 또는 `Space`로 한 번 실행하세요. 고정 주문·`PROD-100`·`qty: 3` 요청이므로 기대 결과는
   세 가지입니다. 400 응답과 재고 부족 사유가 화면에 표시되고, 완료 표시는 나타나지 않아 버튼을
   다시 누를 수 있으며, DB는 `CREATED·2·0` 그대로입니다.
   오류 박스에는 "재고가 부족합니다. (현재 재고: 2, 요청 수량: 3)" 앞뒤로 드라이버 이름과 `CONTEXT`,
   `[SQL: ...]`, 안내 링크가 한 문단으로 이어져 보입니다. 이 API가 DB 예외 문자열 전체를 `detail`에
   담아 보내기 때문입니다. 지금은 재고 부족 사유가 들어 있는지만 확인하세요. 나머지는 사용자에게
   보여 주면 안 되는 내부 정보이며, 11.7에서 한계로 다룹니다.

   ![재고가 부족할 때 오류 사유가 표시되고 승인 버튼은 다시 누를 수 있는 화면](images2/11_chapter11_approve_stock_error.png)

   수량은 3으로 유지하세요. `999`처럼 바꾸면 재고 검사보다 주문 수량 불일치 검사가 먼저 걸립니다.
   마지막으로 이 오류 화면에서 개발자 도구로 화면 너비를 `375px`로 줄여, 주문 정보·버튼·오류 문구가
   겹치거나 잘리지 않고 읽히는지 봅니다. 새 요청 없이 확인만 하고 원래 너비로 돌린 뒤 3번으로 넘어갑니다.
   `375px`은 작은 화면을 대표하는 검증 기준일 뿐 CSS 값이 아닙니다.
3. **같은 화면에서 재시도:** DB만 초기화 SQL로 `CREATED·10·0`으로 되돌립니다.
   **실행 전 예측:** DB만 복원하면 화면의 이전 오류도 바로 사라질까요, 다음 요청 때 지워질까요?
   페이지는 새로고침하지 말고, 오류가 남아 있는 화면에서 한 번 요청하세요. 기대 결과는 이전 오류가
   지워지고, 성공 표시와 버튼 잠금이 나타나며, 응답 200과 DB `PAID·7·1`입니다.
4. **입력 오류:** Swagger의 `POST /orders/approve`에서 고정 주문·상품·수량 3을 기준으로 준비합니다.
   **실행 전 예측:** 수량 0이나 잘못된 UUID는 API와 DB 함수 중 어디에서 먼저 거절하며, DB 값은 바뀔까요?
   먼저 `qty`만 `0`으로 바꿔 요청합니다. 다음에는 `qty`를 3으로 되돌리고 `order_id`만
   `invalid-uuid-string`으로 바꿔 요청합니다. 두 오류는 별도로 확인하며, 각 요청 전후 DB는
   `PAID·7·1`로 같아야 합니다.

422는 요청 형식·값이 맞지 않아 거절됐다는 뜻입니다. 응답의 `detail` 배열에서 오류 위치인
`loc`와 원인인 `msg`를 읽습니다. 전체 JSON을 외우지 말고 어떤 필드가 거절됐는지 확인하세요.

| 요청 | 오류 위치 예시 | 확인할 원인 |
| :--- | :--- | :--- |
| `qty: 0` | `["body", "qty"]` | 수량은 1 이상이어야 함 |
| 잘못된 주문 UUID | `["body", "order_id"]` | UUID 형식이 아님 |

**응답 없는 통신 오류 — 위 입력 오류 실험 뒤에 진행**

DB가 `PAID·7·1`인지 확인한 뒤, 백엔드 터미널에서 `Ctrl+C`로 API를 종료합니다(프론트엔드 서버는 켜 둡니다).
Vue 페이지를 새로고침하고 승인 버튼을 한 번 누르세요. Network에서 HTTP 응답이 오지 않은 실패를 확인하고,
화면에 대체 오류 메시지가 보이는지, 완료 표시 없이 로딩이 끝나는지, DB가 `PAID·7·1` 그대로인지 봅니다.
확인이 끝나면 11.3의 절차로 API를 다시 실행하세요. **이 주문은 이미 승인됐으므로 같은 화면에서 다시
요청하지 마세요.** 서버에 중복 승인 방지가 없어서, 재고가 충분하면 한 번 더 차감됩니다.

통신 오류 실험은 서버에 접속하지 못한 경우만 확인합니다. 서버가 저장을 마친 뒤 응답만 사라지는 상황과
그때의 안전한 재시도는 이 실험의 범위 밖입니다.

**선택 검증 — 저장된 주문과 다른 수량**

Core를 마친 뒤 더 확인하고 싶다면, Swagger에서 고정 주문·상품은 그대로 두고 `qty`만 `4`로 요청해 보세요.
양수라서 입력 검사는 통과하지만, 저장된 주문 수량 `3`과 다르다는 사유로 DB 함수가 거절해 400이 와야 합니다.
요청 전후 DB는 `PAID·7·1`로 같습니다. 정상 요청은 다시 보내지 마세요.
건너뛰었다면 `Not Run`으로 남겨도 Core 완료에는 영향이 없습니다.

**선택 검증 — 중간에 실패하면 앞의 쓰기도 취소되는가**

재고 부족은 첫 쓰기 전에 거절되므로, 이미 쓴 내용이 취소되는지는 보여 주지 못합니다. 원자성을 직접 확인하려면
재고 차감 뒤에 원장 기록이 실패하게 만들어 봅니다. Core를 마친 뒤 시간이 있을 때만 진행하세요.
기록표에 행을 추가할 필요는 없습니다. 수행했다면 아래에서 확인한 쓰기 순서·오류·DB 전후값과
임시 제약 제거 여부를 관찰 기록 아래에 짧게 남깁니다.

> **[심화 학습 프롬프트: 중간 실패 롤백 확인]**
> 아래 SQL은 **Chapter 11 전용 DB**의 SQL Editor에서 직접 실행합니다. AI에게 실행을 맡기지 않습니다.
>
> **실행 전 확인:** 보존한 SQL 실행본에서 재고 `UPDATE`가 원장 `INSERT`보다 앞에 있고,
> 원장 기록 실패를 성공으로 바꾸거나 예외를 삼키는 처리가 없는지 확인합니다. 참조 함수는 이 순서이지만
> AI 생성물의 순서는 다를 수 있습니다. 확인하기 어렵다면 아래 프롬프트로 코드 위치와 이유만 짚게 하세요.
> 순서가 다르거나 실제 적용한 정의가 미확인이면 이 실험은 건너뜁니다. 실험을 위해 정상 코드를 바꿀 필요는 없습니다.
>
> 1. [초기화 SQL](#reset-sql)을 실행하고 [상태 조회](#ch11-state-query)가 `CREATED·10·0`인지 확인합니다.
>    API 서버는 켜 두고 화면 페이지는 새로고침합니다.
> 2. 원장 기록만 실패하도록 임시 제약을 추가합니다. 원장이 비어 있어야 추가할 수 있습니다.
>
>    ```sql
>    ALTER TABLE stock_ledger
>      ADD CONSTRAINT tmp_block_ledger CHECK (qty_change <> -3);
>    ```
>
> 3. 화면에서 승인 버튼을 한 번 누릅니다. 위에서 확인한 순서대로 실행되면 재고 차감 뒤
>    원장 단계에서 `tmp_block_ledger` 위반 오류가 나고 400 응답이 와야 합니다.
> 4. 상태 조회에서 `CREATED·10·0` 그대로인지 확인합니다. 앞서 실행된 재고 변경이 남지 않았다는 결과입니다.
>    PostgreSQL은 함수 호출이 오류로 실패하면 그 호출 안의 앞선 변경도 취소합니다. API의 `rollback()`은
>    실패한 트랜잭션을 정리합니다. 이 관찰값만으로 API의 명시적 `rollback()` 효과를 따로 입증한 것은 아닙니다.
> 5. 예상과 다른 결과가 나왔더라도 임시 제약을 제거하고 초기화 SQL로 되돌립니다.
>
>    ```sql
>    ALTER TABLE stock_ledger DROP CONSTRAINT tmp_block_ledger;
>    ```
>
> 같은 AI 대화에서 다음을 질문해 보세요.
>
> ```text
> 보존한 SQL 실행본과 API 코드를 읽고, 재고 UPDATE가 원장 INSERT보다 앞에 있는지와
> 원장 실패가 호출자에게 전달되는지 코드 위치로 확인해 주세요. 실제 적용 정의가 미확인이면 구분해 주세요.
> 이 순서에서 원장 INSERT가 실패할 때 PostgreSQL의 함수 호출 실패 처리와 API의 rollback이
> 각각 어떤 역할을 하는지 설명해 주세요. DB 불변 관찰만으로 명시적 rollback의 효과를 따로 입증할 수 있는지도 구분해 주세요.
> SELECT로 호출하는 이 함수 내부에서는 COMMIT할 수 없다는 점과,
> API가 별도 SQL 쓰기 사이에 미리 커밋하는 경우의 부분 저장 위험을 구분해 주세요. 코드를 바꾸는 실험은 하지 않습니다.
> 파일 수정·DB 접속·비밀값 읽기는 하지 마세요. (개발 환경: FastAPI + SQLAlchemy + Supabase)
> ```

**요구사항별 검증 범위**

아래 표에서 먼저 **Core 실행 항목**을 확인하세요. 예상 결과와 자신의 관찰 기록을 비교해 판정합니다.

| Core 실행 항목 | 코드에서 확인할 근거 | 직접 확인할 결과 |
| :--- | :--- | :--- |
| API 입력 검사 | 요청 모델의 UUID·수량 제한 | 수량 `0`·잘못된 UUID의 422와 DB 불변 |
| 재고 부족 거절 | SQL의 첫 쓰기 전 재고 검사 | 400과 `CREATED·2·0` 유지 |
| 정상 저장 | SQL의 세 쓰기·API 커밋 | `PAID·7·1`, 11.2의 원장 증감량 `-3` |
| 화면 상태 | 요청 처리·상태 갱신 | POST 한 건·로딩 잠금·성공·오류·같은 화면 재시도 |
| 키보드·작은 화면 | 버튼·결과 표시 | 키보드 실행·375px 가독성 |
| 통신 오류 | 응답 없는 오류의 대체 메시지 처리 | API 종료 후 HTTP 응답 없음·로딩 종료·DB 불변 |

**코드 검토와 선택 실험의 범위:** 코드에 조건이 있어도 실행하지 않은 사례는 실행 검증을 `Not Run`으로 남깁니다.

| 확인할 것 | 코드에서 찾을 근거 | 실행 검증의 한계 |
| :--- | :--- | :--- |
| API의 음수 수량 거절 | 요청 모델의 수량 제한 | Core는 `0`만 실행하며 음수는 미실행 |
| DB 함수의 수량 검사 | NULL·0 이하 수량 거절 | 직접 함수 호출로는 미실행. API의 422가 이 검사의 검증은 아님 |
| 주문 존재·상품·수량 일치 | 주문 조회·불일치 거절 | 수량 불일치만 선택 실험. 주문 없음·상품 불일치는 미실행 |
| 중간 실패 뒤 변경 취소 | SQL 쓰기 순서·예외 전달·API 롤백 | 선택 실험에서만 확인. 명시적 `rollback()`만의 효과를 입증하지 않음 |
| 커밋 실패·세션 정리 | API 예외 처리·세션을 닫는 `finally` | 해당 실패·정리 동작 자체는 실행 검증하지 않음 |
| 주문·재고 행 잠금 | SQL의 두 `FOR UPDATE` | 동시 요청의 대기·처리 결과는 미실행 |
| DB 제약조건 | 재고·주문 수량·상태 CHECK | 이 업무 제약을 위반하는 직접 저장은 미실행 |

Core의 재고 부족은 첫 쓰기 전 거절이며, 저장 후 응답 유실은 통신 오류 실험에 포함되지 않습니다.
인증·회사 격리·서버 중복 승인 방지는 미구현입니다. 위 미실행 사례를 모두 추가 실행해야 Core를 완료하는 것은 아닙니다.

<a id="ch11-manual-record"></a>

**수동 관찰 기록**

키트의 `practice-workspace/ch11/observation_record.md`를 열어 아래 표와 같은 기록표를 사용합니다.
파일이 없다면 `ch11/` 폴더에 같은 이름의 Markdown 파일을 직접 만들고, 아래 표를 복사합니다.
기록 파일이 없다는 이유로 키트를 다시 풀거나 지금까지 만든 코드를 초기화할 필요는 없습니다.
요청 전 DB·응답·화면·요청 후 DB를 칸마다 직접 적고, 이 파일의 수정은 AI에게 맡기지 않습니다.
실험 직후 앞의 다섯 행을 채웁니다. 예상과 같으면 `Pass`, 다르면 `Fail`, 실행하지 않았거나
근거가 부족하면 `Not Run`으로 남깁니다. 마지막 행은 아래 AI 검토와 직접 대조 후 작성합니다.

| 항목 | 실제 응답·화면 상태·DB 전 → 후 | 판정 |
| :--- | :--- | :---: |
| 정상 승인·로딩 잠금 | 11.5의 POST 수·응답·버튼 상태·DB 전후값 | Not Run |
| 화면의 재고 부족 오류 | 400 사유·오류 표시·버튼 잠금 해제·DB 전후값 | Not Run |
| 같은 화면에서 재시도 | 이전 오류 해제·성공 응답·화면·DB 전후값 | Not Run |
| 수량 0 입력 오류 | 422의 qty 오류·DB 전후값 | Not Run |
| 잘못된 UUID 입력 오류 | 422의 order_id 오류·DB 전후값 | Not Run |
| AI 검토·직접 대조 | 확인한 코드·SQL 위치와 관찰값이 일치하는 이유 | Not Run |

기록 파일에 다음 표도 직접 추가하고 화면 요구사항의 실제 확인 결과를 남깁니다.

| 추가 확인 | 실제 관찰·판정 근거 | 판정 |
| :--- | :--- | :---: |
| 키보드 | 버튼 이동·포커스 표시·한 번 실행한 결과 | Not Run |
| 작은 화면 | 375px에서 주문 정보·버튼·오류 문구의 가독성 | Not Run |
| 통신 오류 | HTTP 응답 없음·대체 메시지·로딩 종료·DB 전후값 | Not Run |
| 주문 수량 불일치 (선택) | 400 사유·DB 전후값 또는 미실행 | Not Run |

참조 코드로 복구했다면 기록 파일 맨 아래 복구 표에 사용한 코드와 이유를 적고, 변경한 코드로 관련 실험을 다시 합니다.
기록 파일을 직접 만들었다면 맨 아래에 복구한 단계·사용한 코드·이유·다시 실행한 실험을 적습니다.
재고 부족은 **첫 쓰기 전 거절**입니다. Core 기록이 보여 주는 것은 여기까지입니다. 선택 실험을 수행했다면
중간 실패 뒤 앞선 변경이 남지 않는 결과도 확인한 것이며, 동시 요청·서버의 중복 승인 방지·회사 격리는 검증하지 않았습니다.

### 2차 검증: AI 검토를 실제 코드·관찰값과 대조하기

같은 AI 도구나 새 대화에서 아래 프롬프트를 사용합니다. AI가 보존한 SQL 실행본과 관찰 기록을
직접 읽게 하며, 파일 전문과 비밀값은 붙여 넣지 않습니다.

> **[AI 프롬프트: 연결 코드와 실제 관찰값 대조]**
>
> ```text
> AGENTS.md와 Chapter 11의 실제 API·화면 파일, 변경 전후 diff와 테스트 유무를 조사하세요.
> observation_record.md와 workspace/erp-project/sql/의 SQL 실행본을 읽고, 기록된 실행 순서와 성공 여부를 확인하세요.
> 파일 변경·DB 접속·.env와 비밀값 읽기 및 출력은 하지 마세요.
> Git diff가 없으면 현재 파일의 근거와 이전 버전과의 차이를 확인할 수 있는 범위를 구분하세요.
>
> 내가 직접 작성한 관찰 기록을 다음 코드 근거와 대조하세요.
> 1. 요청 본문이 API 명세와 같고, 양수가 아닌 수량·잘못된 UUID가 DB 호출 전 거절되는가?
> 2. DB 함수 호출 뒤 커밋·롤백·세션 정리가 어떻게 이어지는가?
> 3. 요청 중 잠금, 성공 응답 후 완료, 실패 후 재시도와 이전 오류 해제가 관찰값과 맞는가?
> observation_record.md의 '내가 정한 승인 조건' 세 줄도 위 코드·SQL·실제 관찰값과 대조하세요.
> 빠졌거나 잘못 정한 조건과 그 근거를 알려 주세요. 인증·회사 격리·중복 승인 방지는 필요한 조건과 현재 미구현 상태를 구분하고, 구현 범위를 늘리지 마세요.
>
> DB 함수 정의는 보존한 SQL 실행본과 독자의 실행 기록을 근거로 분석하세요.
> 여러 실행본이 있으면 기록된 순서로 변경을 확인하고, 마지막으로 적용한 함수 정의를 근거로 삼으세요.
> 실행본이나 실행 기록이 없거나 서로 맞지 않으면 정의 미확인으로 보고하고, AI 답변이나 참조 코드를 실행본으로 대신하지 마세요.
> DB에 직접 접속해 현재 정의까지 확인한 것은 아니므로, 보존본·실행 기록에 근거한 검토임을 명시하세요.
> DB 관찰값·코드에서 확인한 사실·추측을 구분하고, 각 실험의 Pass·Fail·Not Run 근거와 누락된 값을 알려 주세요.
> 자동 테스트는 없으면 테스트 없음, 있으면 실제 실행 근거에 따라 Pass·Fail·Not Run으로 따로 보고하세요.
> 실행하지 않은 중간 롤백·동시성·멱등성·회사 격리를 통과로 판정하지 마세요.
> 독자가 직접 대조할 요청 검사·트랜잭션 처리·화면 상태 위치를 각각 하나씩 지정하세요.
>
> observation_record.md의 기본 다섯 행과 추가 확인 표에서 실제 값·판정이 빠진 항목도 알려 주세요.
> ```

AI가 지정한 요청 검사·커밋/롤백·화면 상태 코드를 직접 열어 관찰값과 대조하세요.
11.1에서 정한 세 조건이 각각 어디에 반영됐는지 확인하고, 보완한 조건이 있다면 이유를 세 줄 기록에 덧붙입니다.
코드에서 찾은 조건과 직접 실행해 확인한 범위를 구분해, 마지막 **AI 검토·직접 대조** 행의 판단 근거에 포함하세요.
보존한 SQL 실행본에서도 주문 일치 검사와 첫 쓰기를 찾아봅니다. AI가 실행본과 실행 기록을 확인할 수 없었다면
DB 정의는 "미확인"으로 구분하고, SQL Editor에서 실제 실행한 내용과 직접 대조한 근거를 기록에 남깁니다.

관찰값과 코드가 어긋나면 원인과 최소 수정 범위부터 확인하고, 고친 뒤 관련 실험을 다시 합니다.
근거와 관찰값이 맞으면 마지막 행에 위치·이유와 `Pass`를, 다르면 `Fail`을, 확인하지 못했다면
`Not Run`을 적습니다. AI의 답변만으로 끝내지 말고 11.8에서 직접 최종 판정하세요.

> **[심화 학습 프롬프트: 화면 검증과 방어 범위 점검]**
> 위 검토를 마친 뒤 같은 대화에서 이어서 질문하면, 추가 확인 표의 근거와 화면 잠금의 한계를 점검할 수 있습니다.
> 추가 확인 표(키보드·작은 화면·통신 오류)를 채웠다면 이 프롬프트도 함께 사용하세요.
>
> ```text
> 같은 조건(파일 변경·DB 접속·.env와 비밀값 읽기 금지)으로 이어서 점검해 주세요.
> 1. 화면 잠금과 서버의 중복 승인 방지를 내가 혼동한 부분이 observation_record.md에 있는가?
> 2. 키보드·작은 화면·통신 오류의 실제 관찰 근거가 기록에 있는가? 코드만 보고 화면 검증을 통과로 판정하지 마세요.
> 근거가 없는 항목은 Not Run으로 구분해 알려 주세요.
> ```

---

## 11.7 이 기능의 방어막 적용 여부

> **[선택 읽기]** 실습에서 구현한 장치와 아직 보호하지 못하는 범위를 구분합니다.
> AI 생성물은 실제 코드·SQL을 확인한 뒤 아래 참조 구현의 요약과 비교하세요.

| 방어 장치 | 참조 구현 | 보호하는 것 | 보호하지 못하는 것 |
| :--- | :--- | :--- | :--- |
| 화면 버튼 잠금 | 적용 | 요청 중·승인 완료 후 현재 화면의 추가 클릭 | 새로고침·다른 브라우저·API 직접 요청 |
| API 입력 검사 | 적용 | 잘못된 UUID와 양수가 아닌 수량을 DB 호출 전 거절 | 호출자의 신원·업무 권한 |
| 주문·재고 행 잠금 | 적용 | 검사한 행을 트랜잭션 종료까지 잠가 다른 요청의 변경을 기다리게 함 | 동일 주문의 재승인 |
| DB 함수와 API의 commit/rollback | 적용 | 주문·재고·원장을 같은 트랜잭션으로 확정·취소 | 중복 요청이 같은 업무인지 판단 |
| 수량·상태값 CHECK | 적용 | 음수 재고·0 이하 주문 수량·허용하지 않은 상태값 저장을 차단 | 상태가 바뀌는 순서 검사 |
| 서버 중복 승인 방지·상태 전이 검사 | 미적용 | — | 재고가 충분하면 `PAID` 주문도 다시 차감될 수 있음 |
| 인증·회사 격리 | 미적용 | — | 로그인 여부·회사 소유권·업무 권한 검사 |

**화면·API·DB는 서로 다른 조건을 보호합니다.** 버튼을 잠가도 API 직접 요청은 들어올 수
있고, 주문 행을 잠가도 처리가 끝난 뒤 같은 주문을 다시 승인할 수 있습니다. 같은 요청을
반복해도 업무 결과가 중복되지 않게 하는 성질을 **멱등성**이라고 합니다.

`CHECK (status IN ('CREATED', 'PAID'))`는 허용된 값만 검사합니다. `PAID → PAID` 재승인이나
`PAID → CREATED` 역전이를 막으려면 변경 경로에서 현재 상태와 허용된 다음 상태를 검사해야
합니다. Day 프로젝트에서는 각 업무의 상태·재요청 규칙을 확인합니다.
[상태 전이와 트랜잭션](./11_appendix.md#a-1-시니어-심화-amazon-엔지니어가-시스템을-보는-방식-상태-전이와-트랜잭션)은 부록에서 복습할 수 있습니다.

**오류 응답도 학습용으로 단순화했습니다.** API는 DB 예외 문자열을 `detail`에 담고,
연결 실패 같은 서버 오류도 `400`으로 반환합니다. `hide_parameters=True`는 SQLAlchemy의
매개변수 표시를 숨기지만, DB 예외 본문에 포함된 값이나 SQL·함수 이름까지 제거하지 않습니다.
실제 서비스에서는 사용자용 메시지와 서버 로그를 분리하고 업무 오류와 서버 오류를 구분합니다.

DB 함수를 사용했다는 사실만으로 모든 방어가 완성되지는 않습니다. 이 장에서는 함수의 쓰기를
API가 같은 트랜잭션으로 확정·취소하며, Python에서 직접 처리하더라도 같은 DB 트랜잭션과
필요한 잠금을 사용하면 원자적으로 저장할 수 있습니다. 호출·커밋·롤백과 매개변수 바인딩은
11.3의 핵심 코드에서 다시 확인하세요.

> **[검증 범위]** 위 표는 구현의 요약입니다. 11.6에서 관찰한 재고 부족은 첫 쓰기 전 거절이며,
> 중간 쓰기 실패의 롤백·동시 요청·서버 중복 승인 방지·회사 격리를 검증한 결과가 아닙니다.
> 11.6의 선택 검증을 수행했다면 중간 실패 뒤 앞선 변경이 남지 않는 결과도 관찰한 것입니다.
> API의 명시적 `rollback()`만의 효과를 따로 입증한 것은 아니며, 동시 요청·중복 승인 방지·회사 격리도 검증 범위 밖입니다.

---

## 11.8 마무리: 완성 체크리스트

새 요청을 보내지 않고 [11.6 관찰 기록](#ch11-manual-record)을 근거로 마지막 자가 체크를 합니다.

- [ ] 요청 본문이 화면에서 API로 전달되고 DB 함수 호출·커밋·화면 갱신으로 이어지는 위치를 실제 코드에서 찾았다.
- [ ] 정상 승인·재고 부족·같은 화면 재시도·두 입력 오류의 다섯 행이 실제 응답·화면·DB 값과 함께 `Pass`다.
- [ ] 추가 확인 표의 키보드·작은 화면·통신 오류가 실제 관찰 근거와 함께 `Pass`다. 주문 수량 불일치는 선택 검증이다.
- [ ] 11.1에서 정한 거절 조건·함께 저장할 데이터·완료 시점을 코드·SQL 실행본·실제 관찰값과 대조했고 마지막 행도 `Pass`다.
- [ ] 인증·회사 격리·서버 중복 승인 방지는 미구현이며, 동시 요청은 실행 검증하지 않았음을 구분한다.
- [ ] 중간 실패 뒤 앞선 변경이 남지 않는 결과는 선택 실험을 수행한 경우에만 확인했으며, Core만 수행했다면 미검증임을 구분한다.

**Core 완료:** 위 항목을 확인했다면 주문 승인 한 경로의 DB·API·화면 연동 실습을 마쳤습니다.
필수 항목에 `Fail`·`Not Run`이 있으면 해당 근거와 실행부터 보완합니다.
선택 실험의 `Not Run`은 Core 완료를 막지 않습니다. 완료했다면 바로 아래
[11.9 종료 절차](#ch11-finish)로 이동하세요. 11.7과 11.11~11.13은 선택 복습입니다.

> [!TIP]
> **[코드 비교·복구 안내]**
> 동작이 막히면 실패한 단계의 요청·응답과 아래 참조 코드를 비교하세요.
>
> - [DB 테이블과 함수](#ch11-db-reference)
> - [FastAPI API](#ch11-api-reference)
> - [주문 승인 화면과 앱 연결](#ch11-ui-state-reference)
>
> 기초 실습 키트는 시작 scaffold를 제공합니다. 이 절의 참조 코드와 혼동하지 마세요.
> 개인 코드 전체를 덮어쓰기 전에 다른 점과 수정 이유를 확인하고, 바꾼 코드로 다시 검증합니다.
> 전체 참조 코드의 다운로드 링크와 사용 안내는 [11.11 선택 참조](#ch11-reference-section)에서 확인합니다.

---

## [Day 00 전환 준비 트랙] 기초 실습 결과 보존하기 (11.9)

<a id="ch11-finish"></a>

## 11.9 [실습] Chapter 11 종료 상태 확인

Chapter 11의 폴더와 DB는 복습용으로 보존합니다. 삭제·이름 변경·데이터 복사 없이
Day 00에서 별도 프로젝트를 준비하세요.

<a id="ch11-day-transition"></a>

**Day 프로젝트에서 달라지는 점**

| 항목 | Chapter 11 | Day 프로젝트 |
| :--- | :--- | :--- |
| 작업 폴더 | `ch11/workspace/erp-project/`·`frontend-project/` | Day 00에서 별도로 준비하는 `franchise-erp/backend/`·`frontend/` |
| 실행 방식 | 백엔드·프론트엔드 개발 서버를 개별 실행 | Day 1부터 저장소 루트의 Docker Compose로 실행 |
| DB 접근 | SQLAlchemy 세션으로 PostgreSQL에 직접 연결하고 API에서 commit/rollback | 주요 업무는 Supabase Data API·RPC 사용. 여러 쓰기의 저장 조건은 해당 DB 함수에서 확인 |
| Vue 작성 방식 | Options API의 `data()`·`methods` | 주로 Composition API의 `<script setup>` 사용 |
| 인증·권한 | 구현하지 않음 | Day 2부터 로그인·JWT와 업무별 권한 검사 도입 |

RPC는 DB 함수를 원격 호출하는 방식입니다. 도구가 달라져도
**요청 → 서버 검사 → 저장 결과 → 화면 반영**을 대조하는 원칙은 같습니다.

**Day 진입 전, 세 질문으로 확인하기**

새 코드를 작성하거나 요청을 추가로 보내지 않고, 지금 만든 코드와 위 비교표를 보며 자기 말로 설명해 보세요.
답이 막히면 오른쪽 확인 기준으로 돌아갑니다. Day의 구체적인 구현은 해당 실습에서 확인하면 됩니다.

| 질문 | 확인 기준 |
| :--- | :--- |
| 11장에서는 누가 저장을 확정하며, Day의 RPC에서는 어디를 확인해야 할까요? | 11장은 API의 `commit()`·`rollback()`을 봅니다. Day의 여러 쓰기가 함께 확정·취소되는지는 해당 DB 함수에서 확인합니다. Python 서비스 파일의 존재만으로 판단하지 않습니다. |
| 새로고침 뒤 완료 표시가 사라지면, 주문도 승인 전으로 돌아간 것일까요? | 화면 상태만 초기화됩니다. 11장은 DB 상태 조회로 확인하며, Day 화면은 업무에 맞는 API 재조회로 서버의 최신 상태를 반영합니다. |
| 입고 화면에 성공 메시지가 보이면 재고 저장까지 확인한 것일까요? | 메시지만으로는 부족합니다. 해당 API의 성공 응답과 입고·재고·발주 상태 등 요구된 저장 결과를 함께 대조합니다. 11장의 승인 시 재고 차감을 입고에 그대로 적용하지 않습니다. |

### 1단계. 실행 중인 서버 종료

백엔드와 프론트엔드를 실행한 두 터미널에서 각각 `Ctrl+C`를 눌러 서버를 종료합니다. 종료 뒤
브라우저에서 `http://localhost:8000/docs`와 `http://localhost:5173`이 더 이상 열리지 않는지
확인합니다.

### 2단계. Chapter 11 결과 보존

```powershell
Set-Location C:\erp-book\foundation-lab-kit\practice-workspace\ch11

Test-Path workspace/erp-project/api/main.py
Test-Path workspace/frontend-project/src/components/ApproveOrder.vue
```

두 결과가 `True`인지 확인합니다. 폴더 이름을 바꾸거나 실제 비밀값이 든 `.env`를 복사하지 않습니다.

### 3단계. [필수] Day 00 새 작업 폴더로 이동

두 프로젝트의 위치를 구분하세요.

```text
C:\erp-book\
├─ foundation-lab-kit\  # Chapter 2~11 조사·실습 결과
└─ franchise-erp\       # Day 00~30 전용 새 프로젝트
```

[Day 00 — 실습 시작 가이드](days/day_00_starter_kit.md)에 따라 `franchise-erp`를 준비합니다.

### 4단계. Day 00 진입 전 체크리스트

- [ ] 두 서버를 종료하고 Chapter 11 결과를 원래 폴더에 보존했다.
- [ ] 폴더 이름을 바꾸거나 `.env`·Supabase 데이터를 새 프로젝트에 복사하지 않았다.
- [ ] [Day 00](days/day_00_starter_kit.md)의 저장소 준비 절차로 이동한다.

체크를 마쳤다면 Day 00으로 이동하세요. 아래 두 절은 선택입니다.

### 선택: Chapter 11을 처음부터 다시 실습할 때만 초기화

재실습할 때만 사용합니다. 필요한 코드·SQL·관찰 기록을 보존하고,
PowerShell에서 `foundation-lab-kit` 루트로 이동해 초기화 대상을 미리 확인합니다.

```powershell
./tools/reset_practice_chapter.ps1 -Chapter ch11
```

미리 보기에는 백엔드의 `api/main.py`와 프론트엔드의 `ApproveOrder.vue`가 삭제 대상으로,
`src/App.vue`가 `_starter`의 시작 화면으로 복원될 대상으로 표시됩니다. 모든 경로가
`practice-workspace/ch11` 안에 있는지 확인한 뒤에만 적용합니다.

```powershell
./tools/reset_practice_chapter.ps1 -Chapter ch11 -Apply
```

이 도구는 `.env`·`venv`·`node_modules`를 삭제하지 않으므로 같은 PC에서는 재사용할 수 있습니다.
키트를 공유할 때는 비밀정보와 생성 부산물이 포함되지 않았는지 별도로 확인하세요.

DB 객체도 초기화하려면 현재 접속한 프로젝트가 Chapter 11 전용이고 보존할 데이터가 없는지
다시 확인합니다. 그다음 `workspace/sql/99_reset_lab.sql`의 삭제 대상을 읽고 Supabase SQL
Editor에서 직접 실행합니다. 이 SQL은 Chapter 11 표식이 없으면 중단되며, 이 장에서 만든
`approve_order` 함수와 세 테이블만 삭제합니다. 로컬 초기화 도구가 DB에 자동 접속하는 일은
없습니다.

초기화 후 로컬 시작 scaffold는 다음 명령으로 확인합니다.

```powershell
./tools/verify_practice_chapter.ps1 -Chapter ch11
```

### [선택 미리보기: APIRouter와 Composition API]

Day 소스에서 만날 두 문법을 읽어봅니다. 지금 코드를 변경하지 않습니다.

#### 1. FastAPI APIRouter 구조 (백엔드 모듈화)

`backend/app/main.py`의 등록 부분입니다. 독립 실행용 코드가 아니며 URL은 각 라우터에서 확인합니다.

```python
from app.routers import purchase, inventory

app.include_router(inventory.router)
app.include_router(purchase.router)
```

#### 2. Vue 3 Composition API 구조 (프론트엔드 반응형 코드 격리)

이 장의 Options API는 `data()`와 `methods`로 상태·함수를 나눕니다. Day 화면은 주로
`<script setup>` 안에 상태와 함수를 선언합니다. 같은 로딩 상태를 다음처럼 표현합니다.

```javascript
// Options API의 메서드 안
this.isLoading = true

// Composition API의 스크립트 안: const isLoading = ref(false)로 선언한 경우
isLoading.value = true
```

문법이 달라도 요청 중 잠금과 성공·실패 후 화면 갱신을 확인하는 기준은 같습니다.

---

## 11.10 챕터 11 요약 및 마무리

주문 승인 한 건을 **DB의 검사·저장 → API의 커밋·응답 → 화면의 상태 갱신**으로 연결했습니다.
이제 같은 경로에서 잘못된 입력과 재고 부족이 어디에서 거절되는지, 그때 어떤 데이터가 유지돼야 하는지
코드와 관찰 기록으로 설명할 수 있습니다. 11.1에서 정한 조건을 보완한 이유와 11.8의 완료 체크가 그 근거입니다.
Day에서도 화면의 성공 표시를 해당 API와 저장 결과로 확인하고, AI가 검증했다고 말한 범위를 실제 근거와 대조하세요.

### [Next Step] Day 00: 새 ERP 프로젝트 준비

[Day 00](days/day_00_starter_kit.md)에서 저장소를 준비하고, Day 1부터 실행 환경과 업무 기능을
차례로 완성합니다. 2권에서는 Day 30까지 완성한 모놀리스를 재설계합니다.

---

<a id="ch11-reference-section"></a>

## 11.11 [선택 참조] 코드 비교·복구와 심화 복습

> **[선택 참조]** Core를 완료했다면 읽지 않아도 됩니다. 막힌 단계의 코드를 비교·복구할 때 사용합니다.

전체 참조 코드는 기초 실습 키트의 `chapter-reference/ch11/` 폴더에 포함되어 있습니다.
이미 키트를 준비했다면 추가 ZIP을 받을 필요가 없습니다. 시작 scaffold와 구분해 비교·복구용으로 사용합니다.
`chapter-reference/ch11/README.md`를 읽고 필요한 파일만 비교하세요.

<a id="ch11-db-reference"></a>

**DB 테이블과 함수:** `chapter-reference/ch11/approve_order.sql`에서 주문·재고 검사, 행 잠금과 세 쓰기를 비교합니다.
이미 테이블이 있다면 전체 DDL을 다시 실행하지 말고 현재 객체와 필요한 변경부터 확인하세요.
고정 데이터 등록과 실험별 복원은 11.2와 [초기화 SQL](#reset-sql)을 따릅니다.
참조 SQL을 사용했더라도 실제 성공한 내용은 [SQL 실행본 보존 절차](#ch11-sql-record)에 따라 남깁니다.

<a id="ch11-api-reference"></a>

**API:** `chapter-reference/ch11/main.py`를 `workspace/erp-project/api/main.py`와 비교합니다.
요청 검사·매개변수 바인딩·커밋·롤백·세션 정리를 확인하며, 연결값은 기존 로컬 `.env`를 사용합니다.

<a id="ch11-ui-basic-reference"></a>
<a id="ch11-ui-state-reference"></a>

**화면과 앱 연결:** `chapter-reference/ch11/ApproveOrder.vue`와 `chapter-reference/ch11/App.vue`를
`workspace/frontend-project/src/`의 해당 파일과 비교합니다. 요청·로딩·성공·오류 처리와 카드 등록을 확인합니다.
통신만 되는 기본형으로 되돌리거나 정상 화면을 다시 작성할 필요는 없습니다.

전체 파일을 덮어쓰기 전에 차이와 수정 이유를 확인하세요. 복구에 사용한 파일·이유를 관찰 기록에 남기고,
변경한 코드로 관련 실험을 다시 수행합니다. 내려받은 참조 코드 자체를 실제 실행본이나 검증 완료의 근거로 삼지 않습니다.

> **[심화 학습 프롬프트]**
> Core 완료 뒤 DB 함수와 API의 역할이 더 궁금하면 같은 AI 대화에서 질문하세요.
>
> ```text
> AGENTS.md와 보존한 SQL 실행본·관찰 기록·API 코드를 읽고, Chapter 11에서 실제 사용한 정의를 기준으로 설명해 주세요.
> SQL 실행본을 확인할 수 없다면 정의 미확인으로 구분하세요. 파일 수정·DB 접속·비밀값 읽기는 하지 마세요.
> 1. DECLARE, BEGIN~END, RAISE EXCEPTION은 각각 어떤 역할인가요?
> 2. 주문·재고 행의 FOR UPDATE 잠금은 언제까지 유지되며, 왜 재승인 방지와는 다른가요?
> 3. 첫 쓰기 전 거절과 중간 쓰기 실패 후 취소를 구분하고, 이번 실습에서 실제 관찰한 범위를 알려 주세요.
> 4. Depends(get_db), yield, finally의 세션 정리와 API의 commit/rollback은 어떻게 이어지나요?
> 5. SQLAlchemy text()와 매개변수 바인딩의 역할을 구분하고, CORS 설정이 화면 호출에 필요한 이유를 설명해 주세요.
> (개발 환경: FastAPI + SQLAlchemy + Supabase)
> ```

---

## 11.12 [선택 읽기] 현재 구조가 깨지는 순간

> **[선택 읽기]** 업무와 화면이 늘어날 때 구조를 바꾸는 이유를 살펴봅니다.

Day에서는 업무마다 다른 저장 조건을 다룹니다. 공급사 발주와 가맹점 발주는 별도 흐름이며,
승인 한 번으로 아래 업무가 모두 자동 실행되지는 않습니다.

| 업무 | 이어지는 실습 | 이 장에서 가져갈 질문 |
| :--- | :--- | :--- |
| 공급사 발주·수주 | Day 11~13 | 누가 어떤 상태에서 변경할 수 있는가? |
| 본사 입고 | Day 14 | 입고·재고·발주 상태가 함께 저장되는가? |
| 가맹점 발주·배송·입고 | Day 16~18 | 배송 시작과 입고 확정의 저장 시점은 어떻게 다른가? |
| POS 판매 | Day 20 | 판매와 재고 차감을 함께 처리하는가? |
| 마감·정산 | Day 22·24 | 마감된 거래의 변경을 어떻게 제한하는가? |

공급사 전송·바코드 검수·실시간 배송 추적까지 모두 구현한다는 뜻은 아닙니다. 실제 범위는
[Day별 목차](days/_toc.md)를 기준으로 확인합니다.

### 시나리오 1. main.py 파일 하나가 3,000줄이 되는 날

`api/main.py`에 모든 업무를 덧붙이면 수정 위치를 찾기 어렵고 협업 중 변경 충돌도 늘어납니다.
모놀리스 안에서도 파일을 업무별로 나누고 공통 설정과 입력 규격을 분리할 수 있습니다.

> [!TIP]
> **[Day 프로젝트의 해결책: APIRouter 기반 도메인 분리]**
> `backend/app/routers/`의 `purchase.py`·`inventory.py`·`company.py`가 발주·재고·회사 업무를
> 나누어 담당하고, `backend/app/main.py`가 라우터와 공통 설정을 등록합니다.

### 시나리오 2. 누구나 curl 한 줄로 주문을 승인할 수 있다

11장의 `POST /orders/approve`에는 호출자의 신원·권한 검사가 없습니다. 외부에 공개하면
로그인하지 않은 사람도 요청할 수 있습니다. 아래 주소는 설명용이며 실행하지 않습니다.

```bash
# 로그인하지 않은 외부 공격자가 주문 승인을 직접 호출하는 경우
curl -X POST "https://api.my-monolith-erp.com/orders/approve" \
     -H "Content-Type: application/json" \
     -d '{"order_id": "00000000-0000-0000-0000-000000000001", "product_id": "PROD-100", "qty": 3}'
```

화면 잠금을 거치지 않는 이 요청도 주문·상품·수량이 일치하고 재고가 충분하면 처리됩니다.
서버는 **인증(Authentication: 누구인지 확인)**과 **인가(Authorization: 해당 업무의 권한 확인)**를
각각 수행해야 합니다.

> [!TIP]
> **[Day 프로젝트의 해결책: JWT 인증과 역할 검증]**
> Day 2부터 로그인 성공 시 사용자 식별 정보와 권한을 담은 **JWT(JSON Web Token)**를 발급하고,
> 이후 API에서 토큰과 역할을 검증합니다. 화면 버튼을 숨기는 것만으로 권한을 보호하지 않습니다.

### 시나리오 3. 새로고침 한 번에 증발하는 상태와 화면 간 데이터 불일치

`ApproveOrder.vue`의 `isPaid`·`errorMessage`는 새로고침하면 초기화되지만 DB 상태는 남습니다.
이 장은 주문을 재조회하지 않으므로 초기 화면만 보고 승인 여부를 판단하면 안 됩니다.
주문 목록·상단 건수·대시보드가 같은 변경을 반영하려면 API 재조회·컴포넌트 간 알림·공유 상태 중
업무에 맞는 방법을 정해야 합니다.

> [!TIP]
> **[Day 프로젝트의 해결책: 서버 데이터를 기준으로 화면 상태 갱신]**
> Day 프로젝트에서는 API 응답과 재조회를 기준으로 각 화면의 상태를 갱신합니다. 여러 화면이
> 같은 클라이언트 상태를 공유해야 할 때 전역 Store를 도입할 수 있지만, Pinia 설치 자체를
> Core 완료 조건으로 삼지는 않습니다.

### 현재 단일 흐름의 한계와 Day 프로젝트의 해결책 요약

Day에서도 세 가지를 확인하세요. **수정할 업무를 찾기 쉬운가, 서버가 호출자의 권한을 검사하는가,
화면이 서버의 최신 상태를 반영하는가.** 구체적인 구조는 다음 절에서 선택 복습할 수 있습니다.

---

## 11.13 [선택 읽기] Day 프로젝트 구조 예고 및 2권 연결 고리

> **[선택 읽기]** 실습이 없는 복습 단원입니다. Core를 마쳤다면 바로
> [Day 00](days/day_00_starter_kit.md)으로 이동해도 됩니다.

### A. [선택 복습] Day 프로젝트 구조 미리보기

11장은 SQLAlchemy로 PostgreSQL에 직접 접속하고 API에서 commit/rollback합니다.
Day 프로젝트의 주요 업무 API는 Supabase의 Data API와 **RPC(DB 함수 원격 호출)**를 사용합니다.
여러 쓰기를 함께 확정하는 조건은 해당 DB 함수에서 확인하세요. Python 서비스 파일이 있다는
이유만으로 DB 트랜잭션이 보장되지는 않습니다.

본사 입고의 실제 소스에서 다음 역할을 찾아볼 수 있습니다. 이 표는 지금 파일을 만들거나
옮기라는 지시가 아니라, 해당 Day에서 AI의 조사 결과를 확인할 지도입니다.

| 책임 | 현재 Day 소스에서 확인할 위치 | 확인할 것 |
| :--- | :--- | :--- |
| DB 접근 준비 | `backend/app/core/database.py` | `get_tenant_db`가 사용자 토큰을 전달할 Supabase 클라이언트를 준비함 |
| 입력 검사 | `backend/app/models/inventory.py` | 요청의 필드·타입을 검사하는 Pydantic 모델 |
| HTTP·권한·DB 연결 | `backend/app/routers/inventory.py` | 입고 요청·권한 검사·업무 판단·RPC 호출·응답 변환 |
| 업무 판단 | `backend/app/services/hq_inbound.py` | 조회한 값으로 입고 가능 여부와 저장할 값을 판단 |
| 저장 시점 검사·원자 저장 | [본사 입고 DB 함수](../database/create_hq_inbound_rpc.sql) | 저장 시점에 조건을 다시 검사하고 관련 데이터를 함께 저장 |

### A-2. [선택 복습] Day 종합 실전을 위한 3대 데이터 흐름 뼈대

**요청이 저장과 화면 반영까지 이어지는지**를 다음 순서로 비교하세요.

| 확인 순서 | 11장 | Day의 본사 입고 예 |
| :--- | :--- | :--- |
| 화면 요청 | Axios → `/orders/approve` | 입고 화면 → `/api/v1/stock_inouts/confirm` |
| 서버 검사 | Pydantic 입력 검사 | 입력·로그인·업무 권한·마감·입고 조건 검사 |
| DB 호출 | SQLAlchemy로 `approve_order` 호출 | Supabase 클라이언트로 `fn_confirm_hq_inbound` RPC 호출 |
| 저장 결과 | 주문·재고·원장 | 입고·재고·발주 상태·이벤트 등 해당 업무의 저장 결과 |
| 화면 반영 | 성공·오류 표시 | HTTP 응답 확인, 완료 표시·필요 데이터 재조회 |

이 흐름에서 세 가지를 구분하면 됩니다.

- **API 연결:** URL·본문·응답·DB 변화가 이어지는지 봅니다. 모든 Day가 위 본사 입고와
  같은 처리 순서를 따르거나 Axios를 쓰는 것은 아니므로 해당 소스에서 확인합니다.
- **요청·응답의 필드:** 11장의 `order_id`, `product_id`, `qty`처럼 API가 정한 이름을
  사용합니다. Axios는 `response.data`, fetch는 `response.ok`와 `response.json()`을 확인합니다.
- **화면 상태:** 11장의 고정 주문 화면에는 초기 조회·입력 폼이 없습니다. Day에서는 조회·입력이
  추가되며, 저장 중 잠금·성공 후 재조회·실패 후 입력 보존을 업무별로 검증합니다.

11장의 `PAID`나 승인 시 재고 차감을 모든 업무에 적용하지 않습니다. 발주·배송·입고·판매는
각각 상태와 재고가 바뀌는 시점이 다릅니다. 폴더·실행 방식·Vue 문법·인증의 차이는
[11.9의 비교표](#ch11-day-transition)를, 구조 확장의 이유는 11.12를 참고하세요.

### B. [2권 예고 — Day 30 이후 MSA 분산 아키텍처 리빌딩 개념]

**`corp_id`는 회사 소속을 기록할 뿐, 접근 권한을 검사하지 않습니다.** 이 장에서는 기본값을
`'HQ'`로 두었으며 인증·회사 격리를 구현하지 않았습니다. 여러 회사가 같은 시스템을 사용하는
멀티테넌시에서는 로그인한 사용자가 자기 회사의 허용된 데이터만 다루도록 보호해야 합니다.

PostgreSQL의 **행 단위 보안(RLS)**은 정책으로 행 접근을 제한하는 장치입니다. 다만 정책을
우회할 수 있는 연결 역할도 있으므로, 컬럼이나 정책 하나만으로 회사 격리가 완성되지는 않습니다.
구체적인 설정은 아래 부록에서 읽고, 지금 Chapter 11 DB에 추가하지 않습니다.

2권에서는 Day 30까지 완성한 모놀리스를 더 안전하고 확장 가능한 구조로 재설계합니다.
분산 환경의 설계는 그때 학습하며, 지금은 다음 자료를 모두 읽을 필요가 없습니다.

| 더 확인할 주제 | 읽을 자료 |
| :--- | :--- |
| 상태 전이와 트랜잭션 | [부록 A-1](./11_appendix.md#a-1-시니어-심화-amazon-엔지니어가-시스템을-보는-방식-상태-전이와-트랜잭션) |
| 동시성 결함과 업무 영향 | [부록 C-1](./11_appendix.md#c-1-시니어-심화-동시성-결함이-실제로-어떤-재앙을-부르는가) |
| 2권 아키텍처 학습 순서와 흐름도 | [부록 D-1](./11_appendix.md#d-1-2권에서-다룰-핵심-아키텍처-패턴-로드맵) |
| 회사 격리와 모놀리스·MSA의 차이 | [부록 E](./11_appendix.md#appendix-e-2권-진입-전-모놀리스-vs-msa-아키텍처-전환-대비) |

> **[심화 학습 프롬프트: 업무 흐름 비교]**
>
> ```text
> 11장의 주문 승인과 Day 프로젝트의 발주·입고·판매가 어떻게 다른지 복습하고 싶어.
> Day 저장소가 열려 있다면 AGENTS.md와 목차, 실제 소스를 읽고 설명해줘.
> 아직 저장소가 없으면 일반적인 개념만 설명하고 실제 구현을 추측하지 마.
> 공급사 발주와 가맹점 발주를 구분하고, 배송 시작·입고 확정·판매에서
> 각각 언제 재고와 상태가 바뀌는지 비교해줘. 원자 저장과 중복 요청 방지가
> 어디에서 보장되는지도 근거와 함께 구분해줘.
> 파일 수정·명령 실행·DB 접속은 하지 말고 .env나 비밀값을 읽지 마.
> 확인하지 못한 부분은 미확인으로 표시해줘.
> ```
