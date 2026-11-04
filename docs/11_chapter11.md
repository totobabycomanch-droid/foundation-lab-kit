# Chapter 11. DB-API-화면 3층 연동 실습: 설계를 동작하는 코드로

> **실습 키트:** [기초 실습 환경 준비](01A_foundation_lab_setup.md#kit-download)
> 아직 준비하지 않았다면 [기초 실습 환경 준비](01A_foundation_lab_setup.md)를 먼저 완료하세요.

## 11.0 이 챕터에서 얻는 것

AI와 주문 승인 기능을 DB → API → 화면으로 연결하고, 화면의 결과가 실제 저장 결과와 일치하는지 확인합니다.
DB에서 정상 저장과 중간 실패의 취소를 확인한 뒤, API와 화면을 연결합니다. 재고 부족에서는 오류가 표시되고 DB 값이 유지되는지 봅니다.
마지막에는 AI의 안내로 업무 요구가 구현된 코드를 확인하고, 직접 본 결과로 완성한 기능을 설명합니다.
이 장의 `PAID`와 화면의 `isPaid`는 승인 완료를 나타내는 실습용 이름이며, 실제 결제 연동은 포함하지 않습니다.

**진행 순서:** 환경 준비 → 업무 조건 합의 → 단계별 AI 구현·직접 실행·코드 확인 → 최종 AI 검토 → 업무 보고.
각 실습 직후 핵심 코드를 살펴보고 결과가 나온 이유를 이해합니다. 기록에는 정상 승인과 재고 부족에서 본 사실, DB 중간 실패에서 취소를 확인한 결과만 남깁니다.
기초 키트의 `practice-workspace/ch11/observation_record.md`를 열어 두세요. 실제 관찰값은 독자가 직접 적습니다.

이 장을 마치면 다음을 할 수 있습니다.

- 업무 요청에서 언제 거절하고, 무엇을 함께 저장하며, 언제 완료로 표시할지 정합니다.
- 정상 승인과 재고 부족 상황에서 화면과 API 응답이 DB 결과와 맞는지 확인합니다.
- 관찰한 결과가 나온 이유를 DB·API·화면의 실제 코드에서 찾습니다.
- 회의에서 약속한 내용 중 직접 확인한 결과와 아직 확인하지 못한 범위를 설명합니다.

Vue 화면에는 고정 주문 정보와 승인 결과가 표시됩니다. 실제 저장 결과는 Supabase SQL Editor에서
조회하고, 요청·응답은 브라우저 개발자 도구의 Network에서 확인합니다. 화면의 완료 메시지와 DB 값을
함께 대조하는 것이 이번 실습의 기준입니다.

### [진행 기준] 실습 단계별 완료 결과

**먼저 실행을 준비합니다.** 키트와 Chapter 11 전용 DB 연결을 준비하고 주문 담당자의 요청을 듣습니다.

**DB에서 승인 처리를 만듭니다.** 정상 저장과 중간 실패의 취소를 확인한 뒤 같은 시작값에서 API를 연결합니다.

**API를 거쳐 화면까지 연결합니다.** API 시험 화면인 Swagger에서 요청을 보내고, 이어서 담당자가 사용할 화면에서 같은 결과를 확인합니다.

**재고가 부족할 때도 확인합니다.** 오류와 DB 값 유지를 확인한 뒤 만든 기능을 설명하고 실습을 마칩니다.

위 순서로 11.10까지 진행하면 주문 승인 기능의 연결과 확인을 마칩니다.

이 장은 Vue **Options API**(`data()`와 `methods`로 상태와 함수를 나누는 방식)로 단일 화면을 연결합니다.
중단 후에는 [다시 시작하기](supplements/ch11_environment_setup.md#ch11-resume)의 세 순서로 돌아옵니다.
오류가 나면 [실행 오류 도움말](supplements/ch11_environment_setup.md#ch11-run-help)과 [AI 원인 조사](#ch11-ai-debug)를 사용합니다.

---

## 11.0-ENV 실습 시작 전 환경 구축 (Chapter 11 Supabase 전용)

<a id="ch11-environment"></a>

VS Code에서 기초 실습 키트의 `practice-workspace/ch11/`만 엽니다. `workspace/erp-project/`는
백엔드, `workspace/frontend-project/`는 프론트엔드입니다. Chapter 10의 `erp-mini/`는 복사하지 않습니다.
이 폴더와 DB는 Chapter 11 전용이며, Day 00에서는 별도 저장소를 새 폴더에 준비합니다.

Node.js와 npm은 Chapter 6에서 준비한 환경을 사용합니다.

> [!NOTE]
> **운영체제별 버전 확인**
>
> Windows PowerShell에서는 `node --version`과 `npm.cmd --version`으로 버전을 확인합니다.
> `npm` 실행 시 `npm.ps1`이 차단됐다는 오류가 나면 실행 정책을 바꾸지 말고 `npm.cmd`를 사용하세요.
>
> macOS·Linux에서는 `node --version`과 `npm --version`을 사용합니다.
> 버전을 확인할 수 없다면 [Node.js 준비 절](06_chapter6.md#nodejs-ready)에서 해결한 뒤 돌아오세요.

이번 준비는 **시작 파일 확인 → 실행 도구 설치 → 전용 DB 연결** 순서로 진행합니다.
1~3단계를 마치면 로컬 실행 준비가 끝나고, 4~5단계를 마치면 DB까지 연결됩니다.
두 서버를 켜거나 주문 승인 결과를 확인하는 일은 뒤의 실습에서 진행합니다.
이미 설치와 연결을 마쳤다면 반복하지 말고 [6단계의 준비 완료 기준](#ch11-environment-ready)으로 이동합니다.

### 1단계. 실습에 필요한 시작 파일과 폴더 확인

키트에 실습을 시작하는 데 필요한 파일과 폴더가 들어 있는지 확인합니다.
PowerShell에서 키트의 최상위 폴더로 이동한 뒤 아래 명령을 실행하세요.
키트를 다른 위치에 압축 해제했다면 첫 줄의 경로를 자신의 위치로 바꿉니다.

```powershell
Set-Location C:\erp-book\foundation-lab-kit
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\verify_practice_chapter.ps1 -Chapter ch11
Set-Location practice-workspace/ch11

Test-Path AGENTS.md
Test-Path workspace/erp-project/api/__init__.py
Test-Path workspace/erp-project/.env.example
```

검사 명령은 이 PowerShell 프로세스에서만 스크립트 실행을 허용하며, PC의 실행 정책은 영구 변경하지 않습니다.

**출력 예시:** 앞부분의 파일별 검사 결과는 생략했습니다. 마지막 부분을 아래와 비교하세요.

```text
NOT RUN database execution requires a dedicated disposable lab database
INFO    Preview reset targets with: .\tools\reset_practice_chapter.ps1 -Chapter ch11
ch11 static verification passed.
True
True
True
```

**다음으로 넘어갈 기준:** `ch11 static verification passed.`와 마지막 세 줄의 `True`를 확인합니다.
`NOT RUN`은 DB 실행 검사를 아직 하지 않았다는 안내입니다. 지금은 시작 파일을 확인하는 단계이므로 정상이며,
도구는 DB에 자동 접속하지 않습니다. `INFO`에 표시된 초기화 명령도 지금은 실행하지 않습니다.

세 `Test-Path` 결과 중 하나라도 `False`라면 키트를 새 폴더에 다시
압축 해제해 시작 파일을 확인합니다. 기존 작업이 있는 폴더에 덮어쓰지 않습니다.

### 2단계. 프론트엔드 의존성 설치

현재 위치가 `C:\erp-book\foundation-lab-kit\practice-workspace\ch11`인지 확인합니다.
키트를 다른 위치에 압축 해제했다면 해당 위치의 `practice-workspace/ch11` 폴더에서 시작하세요.
아래 명령은 `workspace/frontend-project` 폴더로 이동한 뒤, 화면 실행에 필요한 패키지를 설치합니다.
제공된 `package.json`과 잠금 파일을 사용하며 새 Vite 프로젝트를 만들지 않습니다.

```powershell
Set-Location workspace/frontend-project
npm.cmd ci
```

**출력 예시:** 패키지 수와 설치 시간은 환경에 따라 다릅니다. 아래 `…`는 달라지는 값이나 생략한 내용을 뜻합니다.

```text
added … packages, and audited … packages in …s
…
npm notice New major version of npm available! …
```

**다음으로 넘어갈 기준:** `npm error` 없이 설치가 끝나고 PowerShell 입력창이 다시 나타나는지 확인합니다.
`npm notice`는 npm의 새 버전을 알리는 안내이며 설치 오류가 아닙니다. 표시되지 않아도 정상입니다.
지금은 npm을 업데이트하지 않고 다음 단계로 진행하세요.

<a id="ch11-python-setup"></a>

### 3단계. 백엔드 가상환경과 의존성 설치

이 실습은 **Python 3.12 준비 → 가상환경 생성 → 활성화 → 버전과 경로 확인 → 패키지 설치** 순서로 진행합니다.
PC에 Python 3.15가 설치돼 있어도 삭제하지 않습니다. Python 3.12를 함께 설치하고, 이 장의 가상환경을 만들 때 지정합니다.
아래 명령은 새 PowerShell 창에서 순서대로 실행하세요. 키트 설치 위치가 다르면 첫 명령의 경로를 바꿉니다.

**(1) 백엔드 폴더로 이동하고 Python 3.12 준비**

```powershell
Set-Location C:\erp-book\foundation-lab-kit\practice-workspace\ch11\workspace\erp-project
```

6장에서 사용한 Python Install Manager로 3.12를 준비합니다. 이미 설치돼 있으면 다시 사용할 수 있습니다.
다음 두 명령을 한 줄씩 실행하고, 첫 명령이 오류 없이 끝난 뒤 두 번째 명령으로 버전을 확인합니다.

```powershell
pymanager install 3.12
pymanager exec -V:3.12 --version
```

**확인할 결과:** `Python 3.12.x`가 출력되면 (2)로 진행합니다. 마지막 숫자는 설치 시점에 따라 다릅니다.

**(2) Python 3.12로 Chapter 11 가상환경 생성**

먼저 `Test-Path .\venv`를 실행합니다. `False`라면 아래 생성 명령으로 진행합니다.
`True`라면 새로 만들지 말고 [기존 가상환경 확인](supplements/ch11_environment_setup.md#ch11-existing-venv)을 따라 버전을 확인하세요.
Python 3.12 환경이면 생성 명령을 생략하고 (3)부터 이어갑니다.

현재 위치가 `workspace\erp-project`인 같은 PowerShell에서 실행합니다.

**가상환경 생성 명령**

```powershell
pymanager exec -V:3.12 -m venv venv
```

**확인할 결과:** 오류 없이 PowerShell 입력창이 다시 나타나면 생성이 끝난 것입니다.
별도의 성공 메시지는 나오지 않을 수 있습니다. 6장의 `.venv`와 달리 이 장의 폴더 이름은 `venv`입니다.

**(3) 현재 터미널에서 가상환경 활성화**

활성화는 이 터미널의 `python` 명령이 가상환경 안의 Python을 사용하도록 실행 경로를 바꾸는 작업입니다.
같은 백엔드 폴더에서 아래 명령을 한 줄씩 실행합니다. 첫 명령에서 확인 질문이 나오면 내용을 확인하고 `Y`를 입력하세요.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

첫 명령은 로컬 스크립트를 실행할 수 있도록 **현재 PowerShell 창에만** 정책을 설정합니다.
창을 닫으면 설정도 사라집니다. `RemoteSigned`는 로컬에서 만든 스크립트의 실행을 허용하고,
인터넷에서 내려받은 스크립트에는 서명을 요구합니다. 자세한 범위는
[PowerShell 공식 안내](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies)를 참고하세요.

**확인할 결과:** 활성화 명령이 오류 없이 끝나면 (4)로 진행합니다.
터미널 앞에 `(venv)`가 표시될 수 있지만, 실제로 선택된 Python은 다음 순서에서 확인합니다.

![가상환경 활성화 터미널 예시](images2/11_chapter11_venv_terminal.png)

**(4) 활성화된 Python의 버전과 경로 확인**

같은 PowerShell 창에서 실행합니다.

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

**출력 예시:** 키트 설치 위치에 따라 경로의 앞부분은 달라집니다.

```text
Python 3.12.x
C:\erp-book\foundation-lab-kit\practice-workspace\ch11\workspace\erp-project\venv\Scripts\python.exe
```

**다음으로 넘어갈 기준:** `Python 3.12.x`와 현재 백엔드 폴더의 `venv\Scripts\python.exe` 경로를 확인합니다.
3.15가 나오거나 경로에 현재 프로젝트의 `venv`가 없으면 패키지를 설치하지 말고 (3)의 활성화 결과부터 다시 확인합니다.

**(5) 확인한 가상환경에 필요한 패키지 설치**

(4)를 통과한 같은 PowerShell 창과 백엔드 폴더에서 실행합니다.

```powershell
python -m pip install -r requirements.txt
```

`python -m pip`는 방금 확인한 Python으로 패키지 설치 도구를 실행한다는 뜻입니다.
`requirements.txt`에는 FastAPI, Uvicorn, SQLAlchemy, psycopg2-binary, python-dotenv가 들어 있습니다.

**확인할 결과:** 설치가 오류 없이 끝나고 PowerShell 입력창이 다시 나타나면 됩니다.
마지막의 pip 새 버전 안내는 설치 오류가 아닙니다.

설치나 활성화가 막히면 [Python 설치·활성화 도움말](supplements/ch11_environment_setup.md#ch11-python-help)에서 해당 증상만 확인합니다.

> [!NOTE]
> **macOS·Linux에서 진행한다면**
>
> Python 3.12를 준비한 뒤 같은 백엔드 폴더에서 `python3.12 -m venv venv`로 만들고,
> `source venv/bin/activate`로 활성화합니다. (4)에서 버전과 `venv/bin/python` 경로를 확인한 뒤 (5)의 설치 명령을 실행합니다.
> 이후 본문의 `& .\venv\Scripts\python.exe`는 `./venv/bin/python`으로 바꿉니다.
> 기존 가상환경은 버전과 경로를 확인하고 사용하며, Windows의 실행 정책 명령은 실행하지 않습니다.

**여기까지의 완료 기준:** 시작 파일 확인, `npm ci`, Python 3.12 가상환경의 패키지 설치를 모두 마쳤습니다.
활성화는 현재 터미널에만 적용되므로 새 터미널에서는 다시 실행합니다.

<a id="ch11-supabase-project"></a>

### 4단계. Supabase 연결 정보 설정

먼저 Chapter 11 전용 Supabase 프로젝트를 준비합니다. Supabase는 PostgreSQL DB와 관리 화면을 함께 제공합니다.
이미 `erp-chapter11-lab` 같은 이름의 전용 프로젝트를 만들었다면 이름을 확인한 뒤 아래 **SQL Editor에서 조회하기**부터 진행합니다.
5장이나 10장의 DB와 섞지 않으며, 별도의 `CREATE DATABASE` 명령은 실행하지 않습니다.

#### 로그인하고 조직 선택하기

1. [Supabase 대시보드](https://supabase.com/dashboard)를 엽니다.
2. 처음 사용하는 독자는 화면의 가입 안내에 따라 계정을 만듭니다. GitHub 로그인이나 이메일 등 화면에서 제공하는 방식을 사용하고, 인증을 완료합니다.
3. 로그인 후 프로젝트 목록으로 이동합니다. 조직 선택 또는 생성 화면이 먼저 나오면 사용할 개인 실습 조직을 선택합니다.
4. 조직이 없다면 **New organization**에서 실습용 조직을 만듭니다. 이름은 `erp-book-lab`처럼 용도를 알아볼 수 있게 정합니다.
   무료 실습을 진행한다면 조직 생성 화면에서 **Free** 플랜인지 확인합니다. 이미 개인 실습용 조직이 있다면 다시 만들지 않아도 됩니다.

조직(Organization)은 프로젝트를 묶어 관리하는 공간입니다. 아직 이 조직을 골랐다는 것만으로 DB가 만들어진 것은 아닙니다.
다음 단계에서 Chapter 11에 사용할 프로젝트를 만듭니다.

**이 단계 완료:** 사용할 조직을 선택했고, 그 조직의 프로젝트 목록을 열 수 있습니다.

#### Chapter 11 전용 프로젝트 만들기

프로젝트 목록에서 **New project**를 선택합니다. 생성 화면에서 다음 항목을 확인합니다.

| 화면의 항목 | 입력하거나 확인할 내용 |
|---|---|
| Organization | 앞에서 선택한 개인 실습용 조직 |
| Project name / Name | `erp-chapter11-lab` |
| Database password | 이 프로젝트의 DB 접속에 사용할 길고 고유한 비밀번호 |
| Region | 현재 위치에서 가까운 지역. 선택 가능한 지역 중 하나를 고릅니다. |

DB 비밀번호는 Supabase 로그인 비밀번호와 별개입니다. 비밀번호를 자동 생성했다면 프로젝트를 만들기 전에 비밀번호 관리 도구에 보관합니다.
메모에는 장별 프로젝트 이름을 함께 적어 두세요. DB 비밀번호를 AI 대화나 실습 결과 파일에 넣지 않습니다.

선택한 조직·프로젝트 이름·지역을 다시 읽고 **Create new project**로 생성을 완료합니다.
생성 중에는 기다렸다가 해당 프로젝트의 관리 화면을 엽니다. 화면에서 준비 중이라고 표시되는 동안 SQL을 실행하지 않습니다.
버튼 위치나 문구가 달라도 ‘새 프로젝트 생성’, ‘DB 비밀번호’, ‘지역’에 해당하는 항목을 찾아 확인합니다.

**이 단계 완료:** Chapter 11의 프로젝트 이름이 보이고, 그 프로젝트의 **SQL Editor**와 **Connect**를 열 수 있습니다.
다른 장이나 실제 업무용 프로젝트가 열려 있다면 다음 단계로 진행하지 않습니다.

프로젝트 생성이 제한되면 [공통 부록의 생성 한도 안내](supplements/supabase_project_setup.md#supabase-project-limit)를 확인합니다.

#### SQL Editor에서 조회하기

1. 화면 상단의 프로젝트 이름이 `erp-chapter11-lab`인지 확인합니다.
2. **SQL Editor**를 열고 **New Query**로 새 쿼리를 만듭니다. SQL을 입력하는 편집 영역과 결과 영역을 구분하세요.
3. 아래 SQL을 편집 영역에 붙여 넣습니다. 코드 블록의 시작·끝에 있는 백틱은 복사하지 않습니다.

```sql
SELECT 1 AS connection_check;
```

4. **Run**을 누릅니다. 여러 SQL 중 일부를 선택한 상태라면 선택한 부분만 실행될 수 있으므로, 이번에는 위 한 문장만 둡니다.
5. 결과 표에서 다음과 같은 값을 확인합니다.

| connection_check |
|---:|
| 1 |

이 결과는 브라우저의 SQL Editor에서 DB 조회가 실행됐다는 뜻입니다. 아직 내 PC의 Python 연결을 확인한 것은 아닙니다.
테이블 생성이나 실습 데이터 입력도 하지 않았습니다. 주문 테이블과 승인 함수는 11.2에서 만듭니다.

본문에서 SQL 파일 실행을 안내하면 아래 순서로 진행합니다. 삭제를 포함하는 SQL이면 본문의 삭제 대상 확인부터 마칩니다.

1. VS Code에서 실행할 `.sql` 파일을 엽니다.
2. 파일의 내용을 **전체 복사**합니다.
3. Supabase SQL Editor에서 **New Query로 새 쿼리 탭**을 엽니다. SQL 파일 하나마다 새 탭을 사용합니다.
4. 복사한 SQL을 새 탭에 붙여 넣습니다. 이전 SQL이 남아 있는 탭에 이어 붙이지 않습니다.
5. 현재 프로젝트가 **Chapter 11 전용 프로젝트**인지 확인합니다.
6. **Run**을 눌러 실행합니다.

오류가 표시되면 다음 SQL로 넘어가지 않고 해당 장의 도움말을 확인합니다.

**이 단계 완료:** 오류 없이 결과 표의 `1`을 확인했습니다.

SQL Editor 사용이 아직 낯설다면 아래 프롬프트로 필요한 설명을 요청하세요.

> **[학습 프롬프트: SQL Editor 사용법 확인하기]**
>
> ```text
> Supabase의 현재 공식 문서를 검색해 SQL Editor에서 새 쿼리를 만들고,
> SQL을 실행한 뒤 결과와 오류를 확인하는 방법을 처음 사용하는 사람에게 설명해 주세요.
> SQL 일부를 선택했을 때 실행 범위가 어떻게 달라지는지도 알려 주세요.
> 공식 출처와 확인 날짜를 함께 제시하고, 웹 검색이 불가능하면 알려 주세요.
> ```

#### Session pooler 연결 주소 확인하기

1. 현재 열린 프로젝트가 **Chapter 11 전용 프로젝트**인지 확인합니다.
2. 화면 상단의 **Connect**를 엽니다.
3. 연결 방식에서 **Session pooler**를 선택합니다. **Transaction pooler**와 구분하세요.
4. 연결 주소의 표시 형식을 고르는 항목이 보이면 **URI**를 선택합니다. URI는 `postgresql://`로 시작하는 **한 줄짜리 DB 연결 주소**입니다.
   이미 이런 주소가 표시돼 있다면 그대로 다음 항목으로 진행하세요.
5. **Connection string** 영역의 **Shared pooler** 아래에서 `postgresql://`로 시작하는 연결 주소를 찾습니다.

아래에서 `.env` 파일을 준비한 뒤, 이 주소를 **처음부터 끝까지 전체 복사**합니다.
주소가 가로로 길게 표시되므로 화면에 보이는 부분만 복사하지 않도록 주의하세요.
**Copy prompt**는 주소가 아닌 AI용 설명을 복사하는 기능이므로 사용하지 않습니다.

![Connect에서 Session pooler와 URI를 선택한 연결 정보 화면](images2/11_chapter11_supabase_connect_pooler.png)

위 그림은 주소를 찾는 위치의 예시입니다. 복사할 때는 자신의 Chapter 11 프로젝트에 표시된 주소를 사용합니다.
Supabase 로그인 비밀번호와 DB 비밀번호는 다릅니다. `https://`로 시작하는 프로젝트 URL이나 API 키도 이번 연결에 사용하지 않습니다.

**로컬 연결 설정:**

백엔드 터미널에서 다음 명령을 실행합니다. 이미 `.env`를 작성했다면 복사 명령은 생략합니다.

```powershell
Copy-Item .env.example .env
```

설정 파일은 `ch11/` 기준 `workspace/erp-project/.env`입니다. VS Code에서 이 파일을 직접 열고 아래 순서로 값을 채웁니다.
AI에게 실제 파일을 읽히지 않습니다.

1. 파일에서 `DATABASE_URL=`로 시작하는 줄을 찾습니다. 완성할 형태는 다음과 같습니다. 아래 예시의 대문자 값은 자신의 값으로 바꿉니다.

   ```dotenv
   DATABASE_URL="postgresql+psycopg2://USER:PASSWORD@HOST:PORT/postgres"
   ```

2. 앞에서 열어 둔 Chapter 11 프로젝트의 **Connection string → Shared pooler**에서
   `postgresql://`로 시작하는 **연결 주소 전체**를 복사해 `DATABASE_URL`의 따옴표 안에 붙여 넣습니다.
   사용자명·호스트·포트는 직접 조합하지 않습니다.
3. 주소 맨 앞의 `postgresql://`만 `postgresql+psycopg2://`로 바꿉니다.
   설치한 `psycopg2-binary` 드라이버로 연결하겠다는 뜻입니다.
4. `[YOUR-PASSWORD]`가 남아 있다면 프로젝트 생성 때 정한 **DB 비밀번호**로 바꿉니다.
   비밀번호에 `@`, `#`, `/` 같은 특수문자가 있으면 바로 아래 방법으로 변환한 값을 넣습니다.
5. 파일을 저장합니다. 주소가 한 줄이고 `postgresql+psycopg2://`로 시작하는지 확인한 뒤 아래 DB 표식 등록으로 이어갑니다.

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

연결 주소의 각 부분이 어떤 역할을 하는지 궁금하다면 아래 프롬프트로 설명을 요청하세요.

> **[학습 프롬프트: DB 연결 주소 이해하기]**
>
> ```text
> Supabase와 SQLAlchemy의 현재 공식 문서를 검색해, 이 실습의
> SQLAlchemy 2.x·psycopg2 환경에서 Session pooler로 연결하는 주소 형식을 설명해 주세요.
> postgresql+psycopg2://의 의미와 사용자명·비밀번호·호스트·포트의 역할,
> 비밀번호에 특수문자가 있을 때 처리하는 방법을 예시 값으로 알려 주세요.
> 실제 연결값이나 .env 파일은 요청하지 마세요.
> 공식 출처와 확인 날짜를 제시하고, 웹 검색이 불가능하면 알려 주세요.
> ```

실제 `.env`와 비밀값은 AI가 읽거나 출력하지 못하게 하고, 채팅·Git·화면 캡처에도 포함하지 않습니다.

> [!IMPORTANT]
> **[직접 실행] Chapter 11 전용 DB 표식 등록**
>
> 1. Supabase에서 현재 프로젝트가 **Chapter 11 전용 프로젝트**인지 확인합니다. 보존할 데이터가 있는 프로젝트라면 실행하지 말고 접속 대상부터 다시 확인합니다.
> 2. VS Code에서 `ch11/` 기준 `workspace/sql/00_initialize_lab.sql`을 열고 내용을 **전체 복사**합니다.
> 3. SQL Editor에서 **New Query로 새 쿼리 탭**을 열고 붙여 넣습니다.
> 4. 프로젝트 이름을 다시 확인한 뒤 **Run**을 눌러 한 번 실행합니다.
>
> **완료 기준:** SQL Editor에 오류 없이 실행이 완료됐다는 결과가 표시됩니다. 조회 SQL이 아니므로 데이터 결과 표가 나오지 않아도 정상입니다.
> 이 SQL은 업무 테이블을 만들지 않고 전용 실습 DB 표식만 기록합니다. 주문 테이블과 승인 함수는 11.2에서 만듭니다.
>
> 장 끝의 객체 제거 SQL은 표식이 없으면 중단되지만, 표식 자체가 DB의 용도를 판별하지는 않습니다.
> 운영 DB나 Day 프로젝트에 실행하지 않습니다.

<a id="ch11-db-check"></a>

### 5단계. DB 연결 확인

백엔드 터미널(`erp-project/` 폴더)에서 기존 `venv`의 Python으로 연결만 확인합니다.

현재 위치가 `workspace/erp-project`인지 확인하고 아래 블록 전체를 PowerShell에 붙여 넣어 실행합니다.
첫 줄은 이전 장의 연결값을 사용하지 않도록 현재 터미널의 `DATABASE_URL`을 해제합니다.

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

**확인할 결과:** `1`이 출력되면 연결 성공입니다. 아래 6단계의 완료 기준으로 진행하세요.

연결에 실패했다면 [DB 연결 실패 도움말](supplements/ch11_environment_setup.md#ch11-db-connection-help)에서 오류 종류를 확인합니다.
실제 연결 주소나 오류 원문은 채팅에 붙이지 않습니다.

**첫 명령으로 연결값을 해제하는 이유**

연결 확인의 첫 명령은 이 장에서 서버를 실행할 때마다 반복됩니다. 이유는 한 가지입니다.
`load_dotenv()`는 터미널에 이미 `DATABASE_URL`이 있으면 `.env`의 값으로 덮어쓰지 않습니다.
이전 장에서 같은 이름의 값을 터미널에 설정해 두었다면, `.env`에 Chapter 11 주소를 적어도
다른 프로젝트에 접속할 수 있습니다. 이 명령은 **현재 터미널의 `DATABASE_URL`만 해제**해
항상 `.env`를 쓰게 합니다. 사용자·시스템 전역 설정은 바꾸지 않으며, 새 터미널을 열면 다시 실행합니다.
macOS·Linux에서는 같은 목적으로 `unset DATABASE_URL`을 실행하고, 위 Python 코드를
`./venv/bin/python`으로 실행합니다.



<a id="ch11-environment-ready"></a>

### 6단계. 실습 동작 최종 체크리스트

- [ ] `npm ci`와 가상환경의 `pip install`이 성공했다.
- [ ] 3단계에서 백엔드 `venv`의 Python 실행 경로를 확인했고, `.env`에 자신의 연결값을 입력했다.
- [ ] 전용 실습 DB에서 표식 SQL을 실행했다.
- [ ] 5단계의 연결 확인에서 `1`이 출력됐다.
- [ ] 두 서버의 포트 `8000`·`5173`을 사용할 수 있고 Supabase 프로젝트가 활성 상태다.

**환경 준비 완료:** 파일 검사와 설치, DB 연결 확인까지 마쳤습니다. 두 서버는 뒤의 API·화면 실습에서 실행합니다.
아직 주문 테이블과 승인 함수가 없는 것이 정상입니다. 이어지는 회의에서 업무 조건을 정하고 11.2에서 첫 승인 결과를 확인하겠습니다.

<a id="ch11-after-environment"></a>

---

## 11.1 전체 그림 먼저: 우리가 만들 것

<a id="ch11-business-conditions"></a>

**처음 전달받은 업무 요청**

> 주문 승인 버튼을 누르면 재고를 차감하고 완료 표시를 해 주세요.

**이 요청에서 무엇이 빠졌을까요?** 바로 구현하기 전에, AI가 임의로 결정하게 될 내용을 생각해 보세요.
예를 들어 재고가 부족할 때도 승인해야 할까요? 떠오른 의문을 바탕으로 다음 회의를 읽어 봅니다.

**조건을 구체화하는 업무 회의**

담당자의 질문에 개발자가 처리 방식을 제안하며, 짧은 요청을 구현할 수 있는 조건으로 구체화합니다.
아래는 학습용 가상 회의입니다. 실제 프로젝트에서는 정해지지 않은 업무 기준을 담당자에게 확인하세요.

> **주문 담당자:** 상품 3개를 주문한 건을 승인하려고 합니다. 버튼을 누르면 재고에서도 빠져야 합니다.
>
> **개발자:** 재고에서 3개를 빼고, 재고가 얼마나 바뀌었는지 원장에 `-3`을 남기겠습니다.
> 주문도 승인 완료로 바꾸겠습니다. **재고·원장·주문은 함께 저장하겠습니다.**
>
> **재고 담당자:** 재고가 2개뿐이면요? 승인만 되거나 재고가 음수가 되면 곤란합니다.
>
> **개발자:** **재고가 부족하면 승인하지 않고, 아무 값도 바꾸지 않겠습니다.** 화면에는 이유를 보여 드리겠습니다.
>
> **주문 담당자:** 버튼을 누르고 나면 처리가 끝났는지도 알아야겠네요.
>
> **개발자:** 처리 중에는 기다리는 표시를 하고, **저장이 끝난 뒤 성공 응답을 받으면 승인 완료로 표시하겠습니다.**
> 실패하면 이유를 보여 주고 다시 요청할 수 있게 하겠습니다.
>
> **주문 담당자:** 그럼 정상 승인과 재고 부족을 직접 보여 주시고, 어디서 처리하는지도 설명해 주세요.
>
> **개발자:** 먼저 DB에서 승인 처리를 만들고, API를 거쳐 화면까지 연결하겠습니다. 말씀하신 결과를 하나씩 확인하겠습니다.

**합의한 내용으로 구현 시작하기**

회의에서 재고·원장·주문을 함께 저장하고, 재고가 부족하면 거절하며, 저장 성공을 확인한 뒤 완료로 표시하기로 했습니다.
VS Code 탐색기에서 지금 연 `ch11/` 폴더 바로 아래의 **`observation_record.md`**를 엽니다.
이 파일은 이번 장의 합의 내용과 직접 실행한 결과를 남기는 기록장입니다.
**회의에서 합의한 승인 조건** 항목의 빈칸 세 개를 아래처럼 채웁니다.

```markdown
- 거절할 요청: 재고가 주문 수량보다 부족하면 승인하지 않는다.
- 함께 저장할 데이터: 재고 차감, 원장 기록, 주문 승인 완료를 함께 저장한다.
- 완료로 표시할 시점: DB 저장이 확정되고 API 성공 응답을 받은 뒤 표시한다.
```

이 세 줄은 회의에서 정한 **구현 기준**입니다. 아직 실행한 결과를 적는 것은 아닙니다.
이전 키트에서 항목 이름이 **내가 정한 승인 조건**으로 되어 있다면 같은 세 빈칸을 사용하세요.
`Ctrl+S`로 저장하고 원고 탭으로 돌아옵니다. 기록 파일은 열어 둔 채, 실습을 마칠 때마다 해당 항목을 채우겠습니다.
이제 이 합의를 기준으로 DB 처리를 만들고 API와 화면을 연결하겠습니다.

**세 약속을 DB·API·화면으로 연결하기**

회의에서 정한 거절 조건·함께 저장할 데이터·완료 시점이 각 층에서 어떻게 이어지는지 봅니다.

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

> **실습 3원칙**
>
> 1. 결과를 모르는 요청은 다시 보내지 않고 마지막 응답과 DB 값을 확인합니다.
> 2. 실험 전에 해당 절의 시작 상태를 확인합니다.
> 3. 예측값이 아니라 직접 관찰한 값만 기록합니다.

현재 화면의 버튼 잠금은 서버의 재승인 방지가 아닙니다. 같은 주문을 다시 요청하면 재고가 또 차감될 수 있으므로
실습에서 안내한 시작값 복원과 요청 순서를 따릅니다.

**같은 승인에서 한 층씩 더 확인하기**

같은 주문을 DB → API → 화면 순서로 승인하지만, 각 단계에서 추가하는 근거는 다릅니다.
시작값을 복원하는 이유는 같은 조건에서 새로 연결한 층을 비교하기 위해서입니다.

**DB에서는 저장 결과를 봅니다.** 주문·재고·원장의 변화와 세 쓰기의 위치를 연결합니다.

**API에서는 요청과 응답을 봅니다.** 성공 응답과 DB 결과를 대조하고 저장 확정 뒤 응답하는 코드를 찾습니다.

**화면에서는 담당자가 보는 결과를 봅니다.** 완료 표시와 성공 응답·DB 결과가 일치하는지 확인합니다.

**재고 부족에서는 거절 결과를 봅니다.** 오류가 표시되고 DB 값이 유지되는지 확인합니다.

<a id="ch11-manual-record"></a>

**실습 직후 같은 이름의 항목에 기록하기**

`practice-workspace/ch11/observation_record.md`에는 다음 다섯 항목이 미리 준비되어 있습니다.
각 실습을 마친 뒤 같은 이름의 항목을 채우세요. 한 칸에 실제로 본 값을 한두 줄로 적으면 됩니다.
DB 값은 **주문 상태 / 재고 / 원장 건수** 순서로 적습니다.

- **DB 정상 승인:** 승인 전후의 DB 값과 원장 증감량을 적습니다.
- **DB 중간 실패:** 오류 사유와 실패 후 DB 값, 임시 제약을 제거한 결과를 적습니다.
- **API 정상 승인:** 응답 상태 코드와 본문, 승인 후 DB 값을 적습니다.
- **화면 정상 승인:** 완료 메시지와 버튼 상태, API 응답, 승인 후 DB 값을 적습니다.
- **재고 부족:** 화면 오류와 버튼 상태, API의 거절 사유, 요청 전후의 DB 값을 적습니다.

각 실습의 기록 위치에 작성 예시가 있습니다. 예시와 실제 결과가 다르면 직접 본 값을 적고, 아직 실행하지 않은 칸은 비워 둡니다.
이전 양식에 기록한 값이 있다면 지우지 말고 해당 항목으로 옮깁니다.

AI에게 아래의 업무 요청을 보내면 키트의 `AGENTS.md`와 연결 명세를 읽고 구현합니다.
독자는 결과를 실행해 보고 기록한 뒤, 마지막에 AI의 안내로 코드를 살펴봅니다.

<a id="ch11-ai-debug"></a>

**막혔을 때:** 현재 단계와 증상을 한 문장으로 정리해 [AI 원인 조사](supplements/ch11_environment_setup.md#ch11-ai-debug-help)를 요청하세요.
예를 들어 “응답은 200인데 화면에 완료 표시가 없습니다”처럼 자신이 본 현상을 알려 주면 됩니다.

---

## 11.2 STEP 1: 주문·재고·원장을 함께 저장하기 (Supabase SQL Editor)

> **[반드시 따라하기]** 테이블·함수를 만들고 정상 저장과 중간 실패의 취소를 확인합니다.

**시작 상태:** 전용 DB 연결 확인을 마쳤고, 이 절의 테이블·고정 데이터는 아직 만들기 전입니다.

### 이번에 만드는 것

“승인하면 재고 3개를 빼고, 원장에 남기고, 주문을 승인 완료로 바꾸겠습니다.” 이제 회의에서 약속한 처리를 DB에 만듭니다.
주문·재고·원장이 모두 저장되거나, 실패하면 앞선 변경도 취소되는 성질을 **원자성**이라고 합니다.
**트랜잭션**은 이처럼 함께 확정(commit)하거나 취소(rollback)할 작업의 단위입니다. 세 변경을 하나로 묶어 보겠습니다.

### AI에게 요청하기

아래 업무 요청을 AI에게 보냅니다. 테이블과 함수의 이름·필드·검사 조건은 키트의 연결 명세를 사용합니다.

> **[AI 프롬프트: 주문 승인 DB 만들기]**
>
> ```text
> AGENTS.md와 connection_spec.md를 먼저 읽고, 회의에서 정한 주문 승인 처리를 만들어 주세요.
> 재고가 충분하면 주문 수량만큼 차감하고, 원장에 기록하고, 주문을 승인 완료로 바꿔 주세요.
> 세 변경은 함께 저장되어야 합니다. 재고가 부족하면 아무 값도 바꾸지 않고 이유를 알려 주세요.
> 키트의 연결 명세와 기존 파일을 확인해 필요한 테이블·함수 생성 SQL을 답변으로 작성해 주세요.
> SQL은 제가 실행하겠습니다. 기존 데이터 삭제나 샘플 데이터 추가는 하지 마세요.
> 회의의 요청이 SQL 어디에 들어 있는지 핵심 위치와 이유를 짧게 설명해 주세요.
> ```

**실행 전에 볼 것:** AI가 생성한 대상이 주문·재고·원장 테이블과 승인 함수인지 확인합니다.
기존 데이터 삭제나 샘플 INSERT가 들어 있다면 실행하지 말고 이유를 확인하세요.
SQL이 길어 위치를 찾기 어렵다면 회의의 요청을 처리하는 부분을 AI에게 짚어 달라고 요청합니다.
아래에서 직접 실행한 뒤 세 값이 바뀌는 핵심 코드를 살펴봅니다.

### 직접 실행하기

**실행 위치:** Chapter 11 전용 Supabase SQL Editor와 VS Code입니다. 아직 두 개발 서버는 실행하지 않습니다.
`CREATED·10·0`은 **주문 상태·재고·원장 건수** 순서입니다.
이번에는 테이블과 데이터를 만든 뒤 `CREATED·10·0 → PAID·7·1 → CREATED·10·0`을 확인합니다.

**(1) 생성 SQL 실행**

Chapter 11 전용 프로젝트의 SQL Editor에서 새 쿼리 탭을 열고, 확인한 AI 생성 SQL 전체를 붙여 넣어 한 번 실행합니다.
오류 없이 완료되면 다음으로 진행합니다. [전체 참조 SQL](#ch11-db-reference)은 실패 원인을 조사할 때만 비교하며 함께 실행하지 않습니다.

<a id="ch11-sql-record"></a>

**(2) 성공한 SQL 실행본 보존**

방금 SQL Editor에서 성공한 테이블·함수 생성 SQL을 그대로 복사해 보존합니다.
다음 단계에서 AI가 이 실행본을 읽고 API를 연결하므로, 실제로 적용한 내용을 남겨 두는 것입니다.

1. VS Code에서 `workspace/erp-project/sql/` 폴더를 만들고 `01_approve_order.executed.sql` 파일에 저장합니다.
2. 고정 데이터 INSERT·승인 호출·초기화 SQL은 이 파일에 섞지 않습니다. 연결 주소와 비밀번호도 넣지 않습니다.
3. `observation_record.md`의 **실제 실행한 SQL**에 파일의 상대 경로와 적용 순서, 성공 여부를 적습니다.

이후 API를 만들 때 AI가 이 파일을 읽습니다. 함수를 수정해 다시 적용했다면 이전 파일은 보존하고,
성공한 변경 SQL을 `02_approve_order.executed.sql`처럼 다음 번호로 저장합니다. 저장한 파일을 다시 실행하지는 않습니다.

**(3) 고정 상품과 주문 등록**

새 쿼리 탭에서 아래 SQL 전체를 최초 한 번만 실행합니다.

```sql
INSERT INTO stock (product_id, quantity) VALUES ('PROD-100', 10);
INSERT INTO orders (order_id, product_id, quantity, status)
VALUES ('00000000-0000-0000-0000-000000000001', 'PROD-100', 3, 'CREATED');
```

오류 없이 등록됐다면 다음 조회에서 실제 값을 확인합니다.

<a id="ch11-db-state-check"></a>
<a id="ch11-state-query"></a>

**(4) 상태 조회 탭 준비와 시작값 확인**

새 쿼리 탭에 아래 조회 SQL만 입력하고 실행합니다. 이후 이 탭을 **상태 조회 탭**이라고 부릅니다.
탭을 열어 두고, 값이 필요할 때 이 조회만 다시 실행합니다.

```sql
SELECT o.status AS order_status, s.quantity AS current_stock,
       (SELECT COUNT(*) FROM stock_ledger
        WHERE product_id = 'PROD-100') AS ledger_count
FROM orders o
JOIN stock s ON s.product_id = o.product_id
WHERE o.order_id = '00000000-0000-0000-0000-000000000001';
```

**확인할 결과:** 다음 한 행이 나와야 합니다. 행이 없다면 다음 승인 호출을 하지 말고 (3)의 등록 결과부터 확인합니다.

| order_status | current_stock | ledger_count |
| :--- | ---: | ---: |
| CREATED | 10 | 0 |

**(5) 수량 3 정상 승인**

**실행 전 예측:** 재고 10개에서 3개를 승인하면 재고와 원장은 어떻게 바뀔까요?
새 쿼리 탭에서 아래 함수를 한 번 호출합니다.

```sql
SELECT approve_order('00000000-0000-0000-0000-000000000001', 'PROD-100', 3);
```

상태 조회 탭으로 전환해 조회 SQL을 실행합니다.

| order_status | current_stock | ledger_count |
| :--- | ---: | ---: |
| PAID | 7 | 1 |

다른 새 탭에서 아래 조회를 실행합니다. 이후 이 탭을 **원장 조회 탭**이라고 부릅니다.

```sql
SELECT qty_change FROM stock_ledger WHERE product_id = 'PROD-100';
```

한 행에 `-3`이면 재고 3개 차감과 원장 기록이 일치합니다. **DB 정상 승인**의 승인 전·승인 후·원장 증감량을 채웁니다.
기록 예시: `승인 전: CREATED / 10 / 0`, `승인 후: PAID / 7 / 1`, `원장 증감량: -3`.

### [실습 공통] 테스트 데이터 초기화 SQL <a id="reset-sql"></a>

**(6) 다음 실습을 위해 시작값으로 복원**

지금은 방금 성공한 승인을 확인했으므로 아래 SQL을 실행합니다. 이후에는 각 실험에서 초기화를 안내할 때만 사용합니다.
새 쿼리 탭에 아래 SQL 전체를 입력합니다. 이후 이 탭을 **초기화 탭**이라고 부릅니다.
Chapter 11 전용 프로젝트인지 확인한 뒤 실행합니다.

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

상태 조회 탭에서 조회를 다시 실행해 복원을 확인합니다.

| order_status | current_stock | ledger_count |
| :--- | ---: | ---: |
| CREATED | 10 | 0 |

테이블과 함수는 유지하며 고정 주문 상태, 상품 재고와 해당 상품의 원장 기록만 되돌렸습니다.
**조회 탭과 초기화 탭은 그대로 열어 둡니다.** 이후 본문에서 탭 이름을 안내하면 해당 SQL Editor 탭을 사용합니다.

**다른 실험에서 이 SQL을 찾아왔다면** 초기화 후 상태 조회로 결과를 확인하고 읽던 실험으로 돌아갑니다.
DB 복원과 Vue 화면 새로고침은 별개이며, **같은 화면 재시도에서는 새로고침하지 않습니다.**
정상 진행 중에는 이어지는 중간 실패 실험과 코드 확인을 마친 뒤 11.3으로 넘어갑니다.

<a id="ch11-db-atomicity"></a>

### 중간에 실패하면 앞선 변경은 어떻게 될까요?

**시작 상태:** 초기화를 마친 DB `CREATED·10·0`. 서버나 화면은 아직 필요하지 않습니다.
정상 승인은 세 쓰기가 모두 성공한 경우였습니다. 이번에는 재고를 차감한 뒤 원장 기록에서 일부러 실패시킵니다.

**(1) 원장 기록을 잠시 막기**

SQL 실행본에서 재고 변경 → 원장 기록 → 주문 완료 순서를 확인합니다. 원장 기록의 실패를 성공으로 바꾸는 예외 처리가 있다면
먼저 AI와 해당 구현을 확인합니다. 이 실험은 예외가 호출자에게 전달되는 함수를 대상으로 합니다.
새 쿼리 탭에서 아래 SQL만 실행합니다. `-3` 기록을 허용하지 않는 임시 검사 조건입니다.

```sql
ALTER TABLE stock_ledger
  ADD CONSTRAINT tmp_block_ledger CHECK (qty_change <> -3);
```

추가에 성공했을 때만 다음으로 갑니다. 이미 같은 이름이 있다면 아래 제거 SQL로 정리한 뒤 시작 상태부터 확인합니다.

**(2) 함수를 호출하고 남은 값 확인하기**

앞의 추가 SQL과 함께 실행하지 말고, 별도 쿼리로 다음 호출만 한 번 실행합니다.

```sql
SELECT approve_order('00000000-0000-0000-0000-000000000001', 'PROD-100', 3);
```

예상 결과는 `tmp_block_ledger` 제약 위반 오류입니다. 상태 조회 탭에서 조회를 다시 실행하면
주문은 `CREATED`, 재고는 `10`, 원장은 `0건`이어야 합니다. 재고를 바꾸는 코드가 먼저 실행됐지만 그 변경도 남지 않았습니다.

**(3) 임시 조건 제거하고 다음 단계로 가기**

결과가 예상과 달라도 아래 SQL은 따로 실행해 임시 조건을 제거합니다. 실험을 중단했다가 돌아온 경우에도 먼저 제거합니다.

```sql
ALTER TABLE stock_ledger DROP CONSTRAINT IF EXISTS tmp_block_ledger;
```

제거 성공과 상태 조회의 `CREATED·10·0`을 확인합니다. 값이 다르면 초기화하기 전에 원인을 확인하세요.
**DB 중간 실패**의 오류 사유·실패 후 DB 값·임시 제약 제거 결과를 채웁니다.
기록 예시: `오류 사유: tmp_block_ledger 제약 위반`, `실패 후 DB 값: CREATED / 10 / 0`, `임시 제약 제거 결과: 오류 없이 완료`.

여러 쓰기를 하나의 작업으로 묶어 모두 저장하거나, 실패하면 앞선 변경까지 취소하는 성질을 **원자성**이라고 합니다.
이번에는 PostgreSQL이 실패한 함수 호출의 앞선 재고 변경을 취소했습니다. API를 거치지 않았으므로 API의 `rollback()`을 실행한 실험은 아닙니다.

<a id="ch11-understand-db"></a>

### 이번에 이해한 것

**질문 하나:** 세 쓰기는 어디에 있으며, 원장 기록이 실패했을 때 앞선 재고 변경은 어떻게 됐나요?
**검색 단서:** SQL 실행본에서 `UPDATE stock`, `INSERT INTO stock_ledger`, `UPDATE orders`를 차례로 검색합니다.
방금 보존한 SQL 실행본을 열어 아래 역할을 찾습니다. 참조 함수의 핵심은 다음 세 쓰기이며,
이 조각만 따로 실행하지 않습니다.

```sql
UPDATE stock SET quantity = quantity - p_qty WHERE product_id = p_product_id;
INSERT INTO stock_ledger (product_id, qty_change, reason)
VALUES (p_product_id, -p_qty, '주문 승인 처리 (' || p_order_id || ')');
UPDATE orders SET status = 'PAID' WHERE order_id = p_order_id;
```

관찰한 재고 `10 → 7`·원장 `-3`·주문 `PAID`를 각 쓰기에 연결하세요.
그 앞에서 수량·주문 일치·재고를 검사하는 곳도 짚습니다. 생성물의 문법이 달라도 같은 역할이면 됩니다.
세 쓰기 사이에 일부만 확정하는 커밋은 없으며, 호출한 트랜잭션에서 함께 확정·취소합니다.

**검사한 재고가 도중에 바뀌면 어떨까요?** `FOR UPDATE`는 조회한 주문과 재고 행을 트랜잭션이 끝날 때까지 잠급니다.
다른 요청이 같은 행을 변경하려면 기다려야 하므로 재고를 검사하는 동안 그 값이 바뀌는 것을 막습니다.
처리가 끝난 뒤 들어오는 같은 주문의 재승인을 거절하는 기능은 별도로 필요합니다.

**이번에 확인한 것:** 정상 호출에서는 세 값이 함께 저장됐고, 원장 기록 실패에서는 앞선 재고 변경도 취소됐습니다.

**다음 단계 조건:** 정상 저장과 중간 실패의 취소를 확인하고, 임시 제약을 제거해 `CREATED·10·0`이 남았다면 11.3으로 넘어갑니다.
고정 주문 UUID·상품·수량은 뒤의 API와 화면에서도 그대로 사용합니다.

---

## 11.3 STEP 2: DB 함수를 호출하는 API 만들기 (FastAPI)

> **[반드시 따라하기]** DB 함수를 호출하는 API를 만들고 Swagger에서 확인합니다.

<a id="ch11-api-prepare"></a>

**시작 상태:** DB `CREATED·10·0`. 아래에서 백엔드 서버를 실행합니다.

### 이번에 만드는 것

DB에서 승인 처리가 되는 것을 확인했습니다. 이제 화면에서도 이 처리를 요청할 수 있게 API를 연결하겠습니다.
API는 요청 형식·수량을 검사하고, 주문 일치·재고 판단과 저장은 앞에서 만든 DB 함수에 맡깁니다.
호출 결과를 응답으로 바꾸는 데 집중하는 구조를 **Thin Layer API(처리 책임을 좁힌 API)**라고 부릅니다.
이 실습에서 DB 함수에 맡기는 이유는 재고 검사와 세 쓰기를 한곳에서 처리해 일부만 저장되지 않게 하기 위해서입니다.
API에는 요청을 받고 결과를 돌려주는 일을 남깁니다. 모든 업무 계산을 DB에 넣어야 한다는 뜻은 아닙니다.

이 장은 DB 응답을 기다리는 동기 호출을 사용하며, API 경로 함수는 일반 `def`로 작성합니다.

브라우저는 화면과 API의 주소가 다르면 응답을 읽어도 되는지 확인합니다. 여기서는 포트 `5173`과 `8000`이 달라 다른 출처로 취급됩니다.
**CORS**는 API가 응답을 읽도록 허용할 화면의 출처를 알려 주는 설정이며, 이 장에서는 `http://localhost:5173`을 허용합니다.
로그인이나 업무 권한 검사와는 다른 역할입니다.

**예상 구현 위치:** `workspace/erp-project/api/main.py`. 시작 키트의 기존 프로젝트에 API를 추가합니다.

### AI에게 요청하기

앞에서 성공한 SQL 실행본을 읽고 API를 연결하도록 요청합니다. 조사와 구현·검사는 한 요청으로 진행합니다.

> **[AI 프롬프트: 승인 처리를 API로 연결하기]**
>
> ```text
> AGENTS.md와 connection_spec.md, 앞에서 실행한 SQL과 관찰 기록을 읽고 승인 API를 만들어 주세요.
> 화면에서 승인 요청을 보내면 앞에서 만든 DB 함수가 처리하게 해 주세요.
> 저장이 끝난 뒤 성공을 응답하고, 잘못된 요청이나 재고 부족은 이유를 알려 주세요.
> 키트 명세의 요청·응답과 허용 범위를 지키며 조사·구현·검사를 진행해 주세요.
> 바꾼 파일과 검사 결과, 실행을 막는 문제만 짧게 알려 주세요.
> ```

**실행 전에 볼 것:** diff(변경 전후의 차이)에서 예상한 백엔드 API 파일이 바뀌었고 구문 검사가 통과했는지 확인합니다.
Git이 없는 폴더라면 AI에게 변경 전후 비교를 요청합니다.
명세 충돌이나 검사 문제가 보고됐다면 해결한 뒤 실행합니다. DB 저장 결과는 아래 Swagger에서 직접 확인합니다.

### 직접 실행하기

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

<a id="ch11-api-run"></a>

**실행 위치: 백엔드 터미널 → Swagger.** DB는 `CREATED·10·0`에서 시작합니다.
성공 응답과 `PAID·7·1`을 확인한 뒤 DB를 복원하고, 백엔드 서버는 켜 둡니다.

1. **백엔드 터미널**에서 아래 첫 명령으로 실행 폴더를 맞춘 뒤 기존 `venv`의 Python으로 서버를 켭니다.
   프론트엔드도 같은 방식으로 폴더를 옮긴 뒤 실행합니다. 키트를 다른 곳에 설치했다면 경로를 바꾸세요.

   ```powershell
   Set-Location C:\erp-book\foundation-lab-kit\practice-workspace\ch11\workspace\erp-project
   Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
   & .\venv\Scripts\python.exe -m uvicorn api.main:app --reload
   ```

   `Remove-Item`은 현재 터미널에 남아 있는 이전 DB 연결값을 해제합니다. `.env` 파일을 지우는 명령은 아닙니다.
   `load_dotenv()`는 기존 환경값을 덮어쓰지 않으므로, 이번 백엔드 폴더의 `.env`를 사용하려고 먼저 해제하는 것입니다.
   macOS·Linux에서는 `ch11/`에서 `cd workspace/erp-project`로 이동하고 `unset DATABASE_URL`을 실행한 뒤
   `./venv/bin/python -m uvicorn api.main:app --reload`로 서버를 실행합니다.

2. `http://localhost:8000/docs`에서 `POST /orders/approve`를 펼치고 **Try it out**을 누릅니다.
   SQL Editor의 **상태 조회 탭**에서 `CREATED·10·0`인지 확인한 뒤 아래 본문을 입력합니다.

   ```json
   {
     "order_id": "00000000-0000-0000-0000-000000000001",
     "product_id": "PROD-100",
     "qty": 3
   }
   ```

3. **실행 전 예측:** 성공 응답은 DB 함수가 반환한 직후와 커밋이 끝난 뒤 중 언제 보내야 할까요?
   회의에서 정한 완료 시점을 떠올린 뒤 **Execute를 한 번만** 누릅니다. 응답 뒤 이 절에서 코드의 순서를 확인합니다.
   응답 `200`·`{"status":"success"}`와 DB 상태 `PAID·7·1`을 대조합니다.
4. <a id="ch11-api-reset"></a>SQL Editor의 **초기화 탭**에서 SQL을 실행하고, **상태 조회 탭**에서 `CREATED·10·0`을 확인합니다. 백엔드 서버는 켜 둡니다.

<a id="ch11-understand-api"></a>

### 이번에 이해한 것

**질문 하나:** 저장 확정과 성공 응답 중 무엇이 먼저인가요?
**검색 단서:** API에서 `commit`, `rollback`, `return`을 검색해 확정·취소·성공 응답의 위치를 찾습니다.
생성한 API를 열어 DB 호출·커밋·성공 반환의 순서를 찾습니다. 참조 코드에서는 다음과 같습니다.

```python
db.execute(
    text("SELECT approve_order(:id, :pid, :q)"),
    {"id": request.order_id, "pid": request.product_id, "q": request.qty}
)
db.commit()
return {"status": "success"}
```

`text()`는 실행할 SQL 객체를 만들고, `:id` 같은 매개변수에 값을 따로 전달합니다.
요청값을 SQL 문장에 직접 이어 붙이지 않습니다. 성공 응답은 `commit()` 뒤에 반환합니다.
함수의 `BEGIN~END`는 실행문을 묶는 블록이며 커밋 명령이 아닙니다.
**API 정상 승인**의 응답 상태 코드와 본문, 승인 후 DB 값을 채웁니다.
기록 예시: `응답 상태 코드와 본문: 200, {"status":"success"}`, `승인 후 DB 값: PAID / 7 / 1`.

**이번에 확인한 것:** 완료 시점 — API로도 저장 결과를 확인하고, 코드에서 커밋 뒤 성공 응답하는 순서를 찾았습니다.

**다음 단계로:** 성공 응답과 DB 결과를 확인하고 시작값으로 복원했다면, 서버를 켜 둔 채 11.4로 넘어갑니다.

**같은 실패 응답이어도 거절한 곳이 다릅니다.** 잘못된 UUID나 수량 0은 Pydantic(요청값의 형식과 범위를 검사하는 도구)이
DB 함수를 호출하기 전에 `422`로 거절합니다. 요청 형식이 맞더라도 재고가 부족하면 DB 함수에서 예외가 발생하고, 이 API는 이를 `400`으로 돌려줍니다.
이 학습용 API는 DB 예외 문자열을 `detail`에 담고 연결 실패 같은 서버 오류도 `400`으로 반환하므로, 상태 코드와 함께 사유를 읽어야 합니다.

---

## 11.4 STEP 3-A: 승인 API를 호출하는 화면 만들기

> **[반드시 따라하기]** 로딩·성공·오류 처리를 포함한 주문 승인 화면을 한 번 생성합니다.

<a id="ch11-ui-prepare"></a>

**시작 상태:** DB `CREATED·10·0`, 백엔드 서버 실행 중.

### 이번에 만드는 것

API에서도 승인 결과를 확인했습니다. 이제 담당자가 버튼을 눌러 그 결과를 볼 수 있게 화면을 만들겠습니다.
회의에서 정한 대로 처리 중에는 기다리는 표시를 하고, 저장 성공은 완료로, 실패는 이유와 함께 보여 줍니다.
이 절에서 화면을 연결하고 이어지는 11.5에서 정상 승인을 한 번 실행합니다.

### AI에게 요청하기

키트는 Vue Options API와 Axios(브라우저에서 API를 호출하는 라이브러리)를 사용합니다.
화면의 고정 주문과 요청 형식은 연결 명세에 있으므로 업무 동작을 중심으로 요청합니다.

> **[AI 프롬프트: 담당자가 사용할 승인 화면 만들기]**
>
> ```text
> AGENTS.md와 connection_spec.md를 읽고, 담당자가 사용할 주문 승인 화면을 만들어 주세요.
> 키트의 고정 주문 정보를 보여 주고, 승인 버튼을 누르면 앞에서 만든 API를 호출해 주세요.
> 처리 중에는 추가 클릭을 막고, 저장 성공 응답을 받으면 완료로 표시하고 버튼 잠금을 유지해 주세요.
> 실패하면 이유를 보여 주고 다시 요청할 수 있게 하며, 새 요청을 시작할 때 이전 오류를 지워 주세요.
> 키트 명세의 오류 안내와 기존 화면·의존성을 지키며 시작 화면에 연결하고 빌드까지 확인해 주세요.
> 바꾼 파일과 빌드 결과, 실행을 막는 문제만 짧게 알려 주세요.
> ```

**실행 전에 볼 것:** 주문 카드를 만들고 `src/App.vue`에 연결했는지 변경 요약을 확인합니다.
예상 위치는 `workspace/frontend-project/src/components/ApproveOrder.vue`와 `src/App.vue`입니다.
빌드가 통과하면 화면을 엽니다. 빌드 성공과 실제 화면 동작은 별도로 확인합니다.
키트의 `workspace/_starter/App.vue`는 시작 화면 복원용이며 개인 작업의 백업은 아닙니다.

### 직접 실행하기

<a id="ch11-ui-run"></a>

1. 11.3의 백엔드 서버는 실행한 채 둡니다. VS Code에서 프론트엔드용 터미널을 별도로 열거나 설치 때 사용한 터미널을 선택합니다.
   아래 첫 명령으로 실행 폴더를 맞춘 뒤 서버를 켭니다. 키트를 다른 곳에 설치했다면 경로를 바꾸세요.

   ```powershell
   Set-Location C:\erp-book\foundation-lab-kit\practice-workspace\ch11\workspace\frontend-project
   npm.cmd run dev -- --port 5173 --strictPort
   ```

   macOS·Linux에서는 `ch11/`에서 `cd workspace/frontend-project`로 이동한 뒤
   `npm run dev -- --port 5173 --strictPort`로 실행합니다.

   이미 5173에서 실행 중이라면 다시 실행하지 않습니다. 포트가 사용 중이면 해당 터미널을 먼저
   확인하세요. `--strictPort`는 다른 포트로 자동 변경되는 것을 막아 API의 허용 주소와 맞춥니다.
2. `http://localhost:5173`에서 주문·상품·수량과 승인 버튼이 보이는지 확인합니다.
   이어지는 11.5의 실행 절차에서 요청·로딩·성공 결과를 확인합니다.

카드가 보이면 이어서 정상 승인을 실행합니다.

---

## 11.5 STEP 3-B: 요청 중 버튼 잠금과 성공·오류 표시 확인하기

> **[반드시 따라하기]** 11.4에서 만든 화면의 상태와 실제 API·DB 결과를 확인합니다.

### 이번에 만드는 것

“저장이 끝난 뒤 승인 완료로 표시하겠습니다.” 담당자가 사용할 화면에서 이 약속을 확인합니다.
정상 승인을 한 번 실행하고, 완료 표시·성공 응답·실제 저장 결과를 대조합니다.
응답·화면·DB 값을 기록한 뒤 아래 코드에서 결과가 나온 이유를 찾습니다.

### 직접 실행하기

<a id="ch11-ui-check"></a>

**시작 상태:** 두 서버 실행 중, DB `CREATED·10·0`.

**실행 전 예측:** 재고 10개에서 3개를 승인하면 어떤 값이 남고 화면에는 무엇이 보여야 할까요?

1. **준비:** 상태 조회 탭의 DB 값이 `CREATED·10·0`인지 확인하고 Vue 페이지를 새로고침합니다.
   Chrome·Edge에서는 `F12` 또는 `Ctrl+Shift+I`로 개발자 도구를 열고 **Network(네트워크)** 탭을 선택합니다.
   Network 상단 도구 모음의 속도 제한 메뉴에서 **No throttling(제한 없음)**을 선택합니다.
2. **실행:** Network 목록의 지우기 버튼으로 이전 기록을 비웁니다.
   [주문 승인 API 호출]을 한 번 누릅니다.
3. **응답 확인:** Network에서 승인 요청의 주소·본문·응답을 확인합니다.

   목록에서 `approve` 중 **Method가 POST인 요청**을 선택합니다. 메서드 열이 보이지 않으면 요청을 열어 Headers의 General에서 확인합니다.
   `OPTIONS`가 함께 보일 수 있는데, 이는 브라우저가 CORS 허용 여부를 미리 묻는 요청입니다. 승인 처리는 `POST`에서 확인합니다.
   아래 탭 이름은 브라우저에 따라 조금 다를 수 있습니다.

   | 볼 곳 | 정상 승인에서 확인할 값 |
   | :--- | :--- |
   | Headers의 General | Request URL은 `http://localhost:8000/orders/approve`, Method는 POST, Status Code는 200 |
   | Payload | 고정 주문의 `order_id`, `product_id: PROD-100`, `qty: 3` |
   | Response | `{"status":"success"}` |

4. **결과 관찰:** 같은 요청의 응답이 `200`이고 본문에 `status=success`가 있는지 확인합니다.
   Vue 화면에 완료 메시지가 나타나고 버튼이 잠긴 채 유지되는지 봅니다. SQL Editor에서도 DB가 `PAID·7·1`로 바뀌었는지 확인합니다.
   11.2에서 준비한 원장 조회 탭에서 `SELECT qty_change FROM stock_ledger WHERE product_id = 'PROD-100';`를 실행해 증감량 `-3`도 확인합니다. 버튼 색상이나 CSS 값까지 참조와 같을 필요는 없습니다.
   성공했을 때 화면은 다음과 같이 보입니다. 디자인이 달라도 완료 메시지와 잠긴 버튼이 있으면 됩니다.

   ![승인 성공 후 완료 메시지와 잠긴 승인 완료 버튼이 표시된 화면](images2/11_chapter11_approve_success.png)

   ![SQL Editor에서 확인한 승인 후 주문 상태와 재고 및 원장 건수](images2/11_chapter11_sql_paid.jpg)

   SQL Editor의 Results에서 `order_status=PAID`, `current_stock=7`, `ledger_count=1`을 확인합니다.
5. **기록:** `observation_record.md`의 **화면 정상 승인** 항목에 완료 메시지와 버튼 상태, API 응답, 승인 후 DB 값을 채웁니다.
   기록 예시: `완료 메시지와 버튼 상태: 승인 완료 표시, 버튼 비활성화`, `API 응답: 200, {"status":"success"}`, `승인 후 DB 값: PAID / 7 / 1`.

**내 말로 설명:** “무엇이 함께 저장됐으며, 화면에서 언제 완료를 확인했나요?”에 자신의 관찰값으로 답합니다.
아래 코드를 읽으며 자신이 본 완료 표시가 어떤 조건에서 나타났는지 연결해 봅니다.

<a id="ch11-understand-ui"></a>

### 이번에 이해한 것

**질문 하나:** 성공 응답은 어디서 화면의 완료 표시로 이어지나요?
**검색 단서:** 화면에서 `status`, `success`, `isPaid` 또는 같은 역할의 상태를 찾습니다.
참조 화면은 성공 응답을 확인한 뒤 완료 상태를 바꿉니다.

```javascript
if (response.status === 200 && response.data.status === 'success') {
  this.isPaid = true;
}
```

이 조건이 성공 응답 뒤 완료 표시로 이어지는지 코드에서 확인합니다. 별도 설명문은 기록하지 않습니다.

**방금 확인한 DB·API·화면 연결을 그림으로 읽기**

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

**이번에 확인한 것:** 화면 연결 — 성공 응답을 받은 뒤 완료 표시가 나타났고 DB 결과도 일치했습니다.

**다음 단계로:** 화면의 완료 표시와 성공 응답이 DB 결과와 맞았다면, 11.6에서 재고 부족 상황을 확인합니다.

---

## 11.6 검증: 내가 만든 것이 제대로 동작하는가

> **[반드시 따라하기]** 재고 부족에서 오류가 표시되고 DB 값이 유지되는지 확인합니다.

“재고가 2개뿐이면 승인하지 않고 아무 값도 바꾸지 않겠습니다.” 이제 이 상황을 직접 눌러 확인합니다.
결과는 열린 `observation_record.md`의 **재고 부족**에 적습니다.
재고 부족 결과를 기록한 뒤 재고를 복원하고 한 번 다시 요청하며 마칩니다.

**시작 준비:** 두 서버가 실행 중이고 11.5의 결과가 `PAID·7·1`로 남아 있습니다.
SQL Editor에는 **상태 조회 탭**과 **초기화 탭**이 열려 있습니다. Vue 화면과 Network도 열어 둡니다.

### 직접 실행하기: 실패와 재시도

<a id="ch11-check-shortage"></a>

**이번에 확인할 것:** 재고가 부족하다는 응답을 받았을 때 화면에도 오류가 나타나고, DB 값은 그대로 남는지 봅니다.

**(1) 재고 2개로 준비**

1. SQL Editor의 **초기화 탭**에서 SQL을 실행합니다.
2. 별도의 새 쿼리 탭에서 아래 SQL을 실행해 재고를 2개로 줄입니다.

   ```sql
   UPDATE stock SET quantity = 2 WHERE product_id = 'PROD-100'
   RETURNING product_id, quantity;
   ```

3. **상태 조회 탭**에서 `CREATED·2·0`을 확인합니다.
4. Vue 페이지를 새로고침하고 Network 기록을 비웁니다. 화면의 요청 수량은 3을 유지합니다.

**(2) 재고 부족 요청과 결과 확인**

**실행 전 예측:** 재고 2개에서 3개를 승인하면 데이터가 바뀔까요?
승인 버튼을 한 번 누르고 다음 결과를 확인합니다.

- Network: 승인 POST의 응답이 `400`이고 `detail`에 재고 부족 사유가 있습니다.
- Vue: 오류 메시지가 보이고 완료 표시 없이 버튼을 다시 사용할 수 있습니다.
- 상태 조회 탭: 조회를 실행하면 `CREATED·2·0` 그대로입니다.

![재고가 부족할 때 오류 사유가 표시되고 승인 버튼은 다시 누를 수 있는 화면](images2/11_chapter11_approve_stock_error.png)

**(3) 기록과 코드 확인**

**재고 부족**의 화면 오류와 버튼 상태, 응답 상태 코드와 오류 사유, 요청 전후 DB 값을 채웁니다.
DB가 요청 전과 같은 `CREATED·2·0`이었는지 실제 조회 결과를 적습니다.
기록 예시: `화면 오류와 버튼 상태: 재고 부족 표시, 버튼 사용 가능`, `응답 상태 코드와 오류 사유: 400, 재고 부족`,
`요청 전후 DB 값: CREATED / 2 / 0 → CREATED / 2 / 0`.
SQL 실행본에서 재고 검사가 첫 쓰기보다 앞에 있는지 확인하고, DB 값이 유지된 결과와 연결해 봅니다.

<a id="ch11-check-retry"></a>

**(4) 재고를 복원하고 마무리**

초기화 탭에서 SQL을 실행해 `CREATED·10·0`으로 복원합니다. 오류 화면은 새로고침하지 않고 승인 버튼을 한 번 누릅니다.
이전 오류가 사라지고 화면에 완료가 표시되는지 봅니다. 성공 응답을 받고 DB도 `PAID·7·1`로 바뀌었다면 마칩니다. 별도 기록은 추가하지 않습니다.

**이번에 확인한 것:** 재고가 부족하면 첫 쓰기 전에 거절돼 DB가 유지되고, 화면에 오류가 표시됩니다.
**종료 상태:** DB `PAID·7·1`, 화면은 완료 상태입니다. 추가 초기화 없이 아래 AI 검토로 이어갑니다.

**기록 확인:** [11.1에서 시작한 기록](#ch11-manual-record)에 정상 승인과 재고 부족의 실제 결과, DB 중간 실패의 메모가 남았는지 확인합니다.

<a id="ch11-ai-review"></a>

### 2차 확인: AI와 기록·코드 검토하기

이제 회의에서 요청한 동작이 어디에 구현됐는지 AI에게 안내받습니다. 같은 대화에서 아래 프롬프트를 실행하세요.
새 대화에서도 SQL 실행본과 관찰 기록을 읽으면 이어갈 수 있습니다.

> **[AI 검토 프롬프트]**
>
> ```text
> Chapter 11의 AGENTS.md와 연결 명세, 관찰 기록을 읽어 주세요.
> 회의에서 약속한 함께 저장·재고 부족 거절·저장 성공 뒤 완료 표시가 현재 코드 어디에 구현됐는지 안내해 주세요.
> 실제 파일 위치와 핵심 코드 몇 줄을 보여 주고, DB 중간 실패의 취소를 포함해 제가 관찰한 결과와 연결하여 쉽게 설명해 주세요.
> 기록과 구현이 다르면 제가 확인할 부분만 짚어 주세요.
> ```

**독자가 마칠 일:** 안내받은 코드를 열어 자신이 본 결과와 연결해 봅니다. 실제 관찰값을 잘못 적었다면 그 부분만 고칩니다.
구현 문제가 발견되면 원인·최소 수정 범위를 확인한 뒤 수정하고 관련 실험을 다시 합니다.
SQL을 바꿨다면 성공한 새 실행본을 보존합니다.

<a id="ch11-code-review"></a>

안내에서 이해되지 않은 곳만 [DB의 세 쓰기](#ch11-understand-db),
[API의 확정·응답 순서](#ch11-understand-api), [화면 잠금](#ch11-understand-ui)으로 돌아가 살펴봅니다.
코드 위치와 설명을 관찰 기록에 다시 옮길 필요는 없습니다.

---

<a id="ch11-defense-scope"></a>

## 11.7 이 기능의 방어막 적용 여부

7A에서 배운 네 방어막을 이번 구현에 대입해 봅시다. 아래는 키트의 참조 구현과 연결 명세를 기준으로 한 요약입니다.
AI가 생성한 코드에서도 같은 역할을 하는 부분을 확인하세요.

| 7A의 방어막 | 이번 구현 | 이 실습에서 확인한 범위 |
| :--- | :--- | :--- |
| 트랜잭션 | DB 함수의 세 쓰기를 함께 확정하거나 취소합니다. API는 성공 시 commit, 예외 시 rollback을 호출합니다. | 정상 저장과 DB 직접 호출의 중간 실패 취소를 확인했습니다. API를 통한 중간 실패 실험은 별도입니다. |
| 동시성 제어 | `FOR UPDATE`로 검사할 주문과 재고 행을 잠급니다. | 코드에서 잠금을 확인했습니다. 동시 요청 실험은 하지 않았습니다. |
| 멱등성 | 서버에서 같은 주문의 재승인을 막는 처리는 없습니다. | 화면의 버튼 잠금만으로 다른 화면이나 API의 재요청까지 막지는 못합니다. |
| 상태 전이 검사 | 현재 주문 상태를 보고 재승인을 거절하는 검사는 없습니다. | 상태값 CHECK는 허용된 값만 검사하며, `PAID` 주문의 재승인을 막지 못합니다. |

인증과 회사별 접근 제한도 이번 구현에 포함하지 않았습니다.
화면의 잠금, API의 입력 검사, DB의 저장 처리는 각각 다른 문제를 막는다는 점을 기억하세요.

---

<a id="ch11-completion"></a>

## 11.8 마무리: 완성 체크리스트

관찰 기록과 AI의 코드 안내를 보며 다음을 확인합니다.

- [ ] DB·API·화면에서 정상 승인을 실행했고, 응답·완료 표시·저장 결과가 일치했다.
- [ ] 재고 부족에서 오류가 표시되고 DB 값이 유지되는 것을 직접 확인했다.
- [ ] DB 중간 실패에서 재고 변경도 취소됐음을 확인하고 임시 제약을 제거했다.
- [ ] AI가 안내한 코드를 열어 결과가 나온 흐름을 설명할 수 있다.

결과가 다르거나 아직 실행하지 않았다면 해당 부분을 확인한 뒤 마칩니다.

<a id="ch11-business-report"></a>

**직접 본 결과로 업무 보고하기**

회의의 담당자에게 결과를 설명할 수 있도록 AI에게 짧은 보고 초안을 요청합니다.

> **[업무 보고 프롬프트]**
>
> ```text
> observation_record.md의 실제 관찰값으로 회의 담당자에게 전할 짧은 업무 보고를 이 대화에 작성해 주세요.
> 정상 승인과 재고 부족의 결과, DB 중간 실패에서 앞선 재고 변경도 취소된 결과를 설명해 주세요.
> 직접 실행한 결과만 확인했다고 표현하고, 코드로만 살펴봤거나 아직 확인하지 못한 범위는 구분해 주세요.
> 기록에 없는 숫자나 검증 결과를 채우지 말고, 파일은 수정하지 마세요.
> ```

초안의 숫자와 확인 범위가 자신이 본 사실과 맞는지 읽고, 자기 말로 설명해 봅니다.
DB 중간 실패의 취소는 SQL Editor에서 확인했습니다. API를 통한 같은 실패 처리와 추가 클릭 차단은 별도로 실행 검증하지 않았으며,
인증·회사 격리·서버 재승인 방지는 구현하지 않았습니다. 보고에서도 이 범위를 지킵니다.

**Core 완료:** 정상 승인과 재고 부족의 결과를 보고, DB 중간 실패에서 앞선 변경도 취소되는 것을 확인했습니다.
이 결과가 코드에서 어떻게 이어지는지 설명할 수 있다면 [11.9 종료 절차](#ch11-finish)로 이동합니다.

---

<a id="ch11-finish"></a>

## 11.9 [실습] Chapter 11 종료 상태 확인

실행 결과를 기록하고 업무 보고의 내용까지 확인했다면 다음 순서로 마칩니다.

1. 백엔드·프론트엔드 터미널에서 각각 `Ctrl+C`로 서버를 종료합니다.
   가상환경을 활성화했다면 같은 터미널에서 아래 명령을 실행하거나 창을 닫습니다.

```powershell
deactivate
```

2. `practice-workspace/ch11/`의 API·화면 코드, 실제 실행한 SQL과 `observation_record.md`를 저장합니다.
   폴더와 DB는 복습용으로 보존합니다.
3. [Day 00 — 실습 시작 가이드](days/day_00_starter_kit.md)에 따라 별도의 `franchise-erp` 폴더에
   새 저장소를 준비합니다. Chapter 11의 `.env`·DB 데이터는 복사하지 않습니다.

---

## 11.10 챕터 11 요약 및 마무리

주문 승인 기능을 DB → API → 화면으로 연결했습니다.
DB에서 주문은 `PAID`, 재고는 `7`, 원장은 `1건`이며 증감량은 `-3`인 것을 확인했습니다. API에서도 성공 응답과 같은 저장 결과를 확인했습니다.
화면에서는 성공 응답 뒤 완료 표시가 나타났고, 재고 부족에서는 오류가 표시되며 DB `CREATED·2·0`이 유지됐습니다.
이로써 회의에서 약속한 정상 저장·재고 부족 거절·저장 성공 뒤 완료 표시를 직접 확인했습니다.
DB에서는 원장 기록을 실패시켜 앞선 재고 변경도 취소되는 원자성을 확인했습니다.
직접 본 결과를 기록하고, AI의 안내로 업무 요청이 구현된 코드와 연결했습니다.

Day에서는 이 작은 예제를 더 많은 업무로 넓힙니다. 화면은 `<script setup>`을 사용하는 **Composition API** 방식도 만나게 됩니다.
이 장에서 `data()`와 `methods`로 나눴던 상태와 함수를 다른 문법으로 구성하지만, 요청을 보내고 결과를 표시하는 역할은 같습니다.
백엔드도 `main.py` 한 파일에서 업무별 API를 받는 `routers/`와 업무 판단을 담는 `services/`로 나뉩니다.
파일이 늘어나도 요청 → 서버 검사 → 저장 결과 → 화면 반영의 흐름을 따라가면 됩니다.

[Day 00](days/day_00_starter_kit.md)에서 새 저장소를 준비하세요. 2권에서는 Day 30까지 완성한 모놀리스를 재설계합니다.

---

<a id="ch11-reference-section"></a>

## 11.11 [선택 참조] 코드 비교·복구와 심화 복습

더 궁금한 질문이 생기면 아래에서 하나를 고릅니다. 연결된 자료에 설명을 요청할 프롬프트와 실험·복원 절차가 있습니다.

<a id="ch11-mid-write"></a>
<a id="ch11-check-input"></a>

| 더 알아보고 싶은 질문 | 사용할 심화 자료 |
| :--- | :--- |
| DB에서 본 중간 실패를 API와 화면으로 확인하면 어떨까? | [중간 실패의 API·화면 처리](supplements/ch11_review.md#ch11-mid-write) |
| 버튼을 잠그면 서버의 재승인도 막힐까? | [화면 잠금과 서버 재승인](supplements/ch11_review.md#ch11-reapprove) |
| 응답을 받지 못하면 다시 눌러도 될까? | [통신 오류와 저장 결과](supplements/ch11_review.md#ch11-network-error) |

다른 질문은 [심화 자료의 전체 목록](supplements/ch11_review.md)에서 찾습니다.

**막힌 코드만 비교·복구하기**

원인이 불분명하면 [AI 원인 조사](#ch11-ai-debug)로 좁힙니다. 참조 코드로 복구할 때는
전체 파일을 덮어쓰기 전에 차이와 수정 이유를 확인하고, 변경한 부분의 실험을 다시 합니다.

<a id="ch11-db-reference"></a>

- [DB 테이블·함수 참조와 SQL 보존](supplements/ch11_review.md#ch11-db-reference)

<a id="ch11-api-reference"></a>

- [API 참조](supplements/ch11_review.md#ch11-api-reference)

<a id="ch11-ui-basic-reference"></a>
<a id="ch11-ui-state-reference"></a>

- [화면·앱 연결 참조](supplements/ch11_review.md#ch11-ui-state-reference)

## 11.12 [선택 읽기] 현재 구조가 깨지는 순간

업무가 늘어나면 수정 위치·호출자 권한·화면 상태는 어떻게 달라질까요?
[구조의 한계 하나 읽기](supplements/ch11_review.md#ch11-expansion)에서 궁금한 문제 하나를 고릅니다.

## 11.13 [선택 읽기] Day 프로젝트 구조 예고 및 2권 연결 고리

<a id="ch11-day-source-map"></a>

<a id="ch11-day-transition"></a>

[Chapter 11과 Day의 구조 비교](supplements/ch11_review.md#ch11-day-transition)와
[실제 소스 지도·2권 연결](supplements/ch11_review.md#ch11-day-source-map)을 필요한 때 읽습니다.
