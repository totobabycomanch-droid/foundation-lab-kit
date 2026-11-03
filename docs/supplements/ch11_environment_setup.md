# Chapter 11 환경 준비

VS Code에서 기초 실습 키트의 `practice-workspace/ch11/`만 엽니다. `workspace/erp-project/`는
백엔드, `workspace/frontend-project/`는 프론트엔드입니다. Chapter 10의 `erp-mini/`는 복사하지 않습니다.
이 폴더와 DB는 Chapter 11 전용이며, Day 00에서는 별도 저장소를 새 폴더에 준비합니다.

Node.js와 npm은 Chapter 6에서 준비한 환경을 사용합니다. `node --version`이나 `npm --version`이
실행되지 않으면 [Node.js 준비 절](../06_chapter6.md#nodejs-ready)에서 해결한 뒤 돌아오세요.

이번 준비는 **시작 파일 확인 → 실행 도구 설치 → 전용 DB 연결** 순서로 진행합니다.
1~3단계를 마치면 로컬 실행 준비가 끝나고, 4~5단계를 마치면 DB까지 연결됩니다.
두 서버를 켜거나 주문 승인 결과를 확인하는 일은 뒤의 실습에서 진행합니다.

## 1단계. 시작 scaffold 확인

scaffold는 실습을 시작할 파일과 폴더의 뼈대입니다. PowerShell에서 키트 루트로 이동해 확인합니다.
실제 설치 위치가 다르면 아래 경로를 자신의 위치로 바꾸세요.

```powershell
Set-Location C:\erp-book\foundation-lab-kit
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\verify_practice_chapter.ps1 -Chapter ch11
Set-Location practice-workspace/ch11

Test-Path AGENTS.md
Test-Path workspace/erp-project/api/__init__.py
Test-Path workspace/erp-project/.env.example
```

검사 명령은 이 PowerShell 프로세스에서만 스크립트 실행을 허용하며, PC의 실행 정책은 영구 변경하지 않습니다.
DB 실행 항목의 `Not Run`(실행하지 않아 아직 판정하지 않았다는 표시)은 오류가 아닙니다. 도구는 DB에 자동 접속하지 않습니다.
세 `Test-Path` 결과는 모두 `True`여야 합니다. 하나라도 `False`라면 키트를 새 폴더에 다시
압축 해제해 시작 파일을 확인합니다. 기존 작업이 있는 폴더에 덮어쓰지 않습니다.

## 2단계. 프론트엔드 의존성 설치

같은 터미널에서 실행합니다. 제공된 `package.json`과 잠금 파일을 사용하며 새 Vite 프로젝트를 만들지 않습니다.

```powershell
Set-Location workspace/frontend-project
npm.cmd ci
```

<a id="ch11-python-setup"></a>

## 3단계. 백엔드 가상환경과 의존성 설치

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
기존 환경을 삭제하거나 재설치하기 전에 [6장의 가상환경 준비·오류 진단](../06_chapter6.md#ch6-verify-venv)을 참고합니다.
6장의 `.venv`와 달리 이 장의 폴더 이름은 `venv`입니다.

macOS·Linux에서는 같은 폴더에서 `python3 -m venv venv`로 만들고,
`./venv/bin/python -m pip install -r requirements.txt`로 설치합니다. 이후 Python 실행에도
Windows의 `& .\venv\Scripts\python.exe` 대신 `./venv/bin/python`을 사용합니다.

활성화는 선택입니다. PowerShell에서 `.\venv\Scripts\Activate.ps1`을 실행하면 아래 그림처럼
`(venv)`가 표시될 수 있지만, 표시 여부는 완료 조건이 아닙니다. 실행 정책으로 차단되면 정책을
변경하지 않고 위의 Python 직접 실행 방식을 사용하세요.

![가상환경 활성화 터미널 예시](../images2/11_chapter11_venv_terminal.png)

`requirements.txt`에는 FastAPI·Uvicorn·SQLAlchemy·psycopg2-binary·python-dotenv가 들어 있습니다.
설치에 실패하면 의존성 파일을 바꾸기 전에 오류 메시지와 가상환경·네트워크·Python 버전을 확인합니다.

**여기까지의 완료 기준:** 시작 파일 확인과 `npm ci`·`pip install`이 모두 성공했다면 로컬 준비는 끝났습니다.
잠시 멈춘다면 마지막 완료 단계를 기록하세요. 다음에는 백엔드 폴더에서 기존 `venv`의 Python을 사용해 4단계부터 이어갑니다.

<a id="ch11-supabase-project"></a>

## 4단계. Supabase 연결 정보 설정

**Chapter 11 전용 프로젝트 준비:** [공통 부록 — Supabase 전용 실습 프로젝트 준비](../supplements/supabase_project_setup.md)를 따릅니다.
이 장의 프로젝트 이름은 `erp-chapter11-lab`처럼 정하고, 5장·10장의 프로젝트와 따로 만듭니다.
이미 Chapter 11 전용 프로젝트가 있다면 다시 만들지 말고 해당 프로젝트를 확인합니다.

공통 부록의 1~4단계에서 프로젝트 생성·SQL Editor 조회·Session pooler 주소 확인을 마칩니다. 비밀번호 처리나 생성 한도에 막히면 5~6단계도 확인합니다.
준비를 마치면 부록 위쪽 표 또는 마지막 **‘본문으로 돌아가기’**에서 **‘Chapter 11 환경 준비 4단계로 돌아가기’** 링크를 눌러 이 단계로 돌아옵니다.
생성 한도 때문에 막혔다면 [프로젝트 생성 한도 안내](../supplements/supabase_project_setup.md#supabase-project-limit)를 확인하세요.
이 장의 테이블과 승인 함수는 11.2에서 만듭니다. 프로젝트 생성만으로 실습 테이블이 생긴 것은 아닙니다.

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

**비밀번호에 특수문자가 있을 때:** [공통 부록의 URL 인코딩 설명](../supplements/supabase_project_setup.md#supabase-password-encoding)을 읽고, 백엔드 폴더의 로컬 터미널에서 아래 명령을 직접 실행합니다.
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

Connect 화면을 찾기 어렵다면 [공통 부록의 연결 화면 예시](../supplements/supabase_project_setup.md#supabase-connect)를 확인합니다.
사용자명과 호스트는 자신의 Chapter 11 프로젝트 화면에서 복사합니다.

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

<a id="ch11-db-check"></a>

## 5단계. DB 연결 확인

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

`1`이 출력되면 연결 성공입니다. 실패하면 위 코드는 오류 종류만 표시합니다. 다음 순서로 확인하세요.

1. `.env`의 `DATABASE_URL`이 비어 있지 않고, 연결 화면에서 복사한 값과 같은가?
2. [Supabase 대시보드](https://supabase.com/dashboard)에서 프로젝트가 일시 중지되지 않았는가?
3. 드라이버 모듈 오류라면 URL의 `+psycopg2`와 가상환경 설치를, `OperationalError`라면
   호스트·사용자명·포트와 네트워크 상태를 확인합니다.

연결 확인이 성공한 뒤 다음으로 진행합니다. 연결값이나 오류 원문은 채팅에 붙이지 않습니다.

## 6단계. 실습 동작 최종 체크리스트

- [ ] `npm ci`와 가상환경의 `pip install`이 성공했다.
- [ ] 3단계에서 백엔드 `venv`의 Python 실행 경로를 확인했고, `.env`에 자신의 연결값을 입력했다.
- [ ] 전용 실습 DB에서 표식 SQL을 실행했다.
- [ ] 5단계의 연결 확인에서 `1`이 출력됐다.
- [ ] 두 서버의 포트 `8000`·`5173`을 사용할 수 있고 Supabase 프로젝트가 활성 상태다.

**환경 준비 완료:** 위 항목을 모두 확인했다면 본문으로 돌아갑니다. 이 장에서 설치와 연결 설정이
가장 번거로운 구간이 끝났습니다. 지금부터는 SQL 실행, Swagger 요청, 브라우저 화면처럼 결과가 눈에 바로 보이는
실습입니다. 연결 확인의 `1`은 DB와 통신했다는 뜻입니다.
주문 테이블·승인 함수는 아직 없는 것이 정상이며, 11.2에서 만들어 첫 승인 결과를 확인합니다.


## 중단 후 다시 시작할 때

<a id="ch11-resume"></a>

멈추기 전에는 마지막으로 완료한 STEP, 사용한 SQL 실행본과 코드를 보존하고,
마지막 응답·DB 상태·다음에 할 실험을 [관찰 기록](../11_chapter11.md#ch11-manual-record)에 적습니다. 연결값은 기록하지 않습니다.
SQL 실행본은 [11.2의 보존 절차](../11_chapter11.md#ch11-sql-record)에 따라 백엔드의 `sql/` 폴더에 남깁니다.
다시 시작할 때는 다음 순서로 확인하세요.

1. VS Code에서 기존 `practice-workspace/ch11/`을 열고 마지막 완료 STEP과 다음 실험을 확인합니다.
   설치를 마쳤다면 `npm ci`·가상환경 생성·패키지 설치를 처음부터 반복할 필요는 없습니다.
2. Chapter 11 전용 Supabase 프로젝트가 활성 상태인지 확인합니다. 일시 중지됐다면 대시보드에서
   해당 프로젝트를 선택해 **Resume project**로 재개하고, 이 문서 5단계의 연결 확인을 다시 합니다.
   복원 방법과 가능 기간은 [공식 일시 중지 안내](https://supabase.com/docs/guides/platform/free-project-pausing)를 확인하세요.
3. 11.2에서 테이블과 고정 주문까지 만들었다면 [상태 조회](../11_chapter11.md#ch11-state-query)로 현재 값을 읽습니다.
   새 실험은 해당 절에서 요구하는 시작 상태로 맞춥니다. 아직 생성하지 않은 객체의 조회·초기화는 실행하지 않습니다.
4. API 실험부터는 11.3의 백엔드 실행 절차를, 화면 실험부터는 11.4의 프론트엔드 실행 절차도 따릅니다.
   새 백엔드 터미널에서도 기존 `venv`의 Python을 직접 사용하고, 본문 11.3의 실행 명령대로 현재 터미널의 `DATABASE_URL`만 해제합니다.
   서버가 이미 실행 중이라면 중복 실행하지 않습니다.
5. 새 화면 실험은 DB 시작 상태를 확인한 뒤 페이지를 새로고침합니다. 단, 11.6의 **같은 화면에서 재시도**는
   오류 화면을 유지한 채 DB만 복원합니다. 브라우저를 닫아 오류 화면이 사라졌다면 재고 부족 실험부터 다시 수행합니다.

기록과 현재 값이 다르면 승인 요청을 추가로 보내지 말고 마지막 실행 결과부터 확인합니다.
DDL을 다시 실행하거나 전체 초기화로 돌아가기 전에, 멈춘 단계의 **[막혔을 때]** 안내를 확인하세요.

[본문으로 돌아가기: 데이터 복원 안내와 11.1 업무회의](../11_chapter11.md#ch11-after-environment)
