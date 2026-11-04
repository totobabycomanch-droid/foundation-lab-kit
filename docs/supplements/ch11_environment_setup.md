# Chapter 11 환경 준비

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
> 버전을 확인할 수 없다면 [Node.js 준비 절](../06_chapter6.md#nodejs-ready)에서 해결한 뒤 돌아오세요.

이번 준비는 **시작 파일 확인 → 실행 도구 설치 → 전용 DB 연결** 순서로 진행합니다.
1~3단계를 마치면 로컬 실행 준비가 끝나고, 4~5단계를 마치면 DB까지 연결됩니다.
두 서버를 켜거나 주문 승인 결과를 확인하는 일은 뒤의 실습에서 진행합니다.
이미 설치와 연결을 마쳤다면 다시 만들지 말고 아래 6단계의 완료 기준으로 확인합니다.

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

> [!NOTE]
> **이 폴더에서 가상환경을 만든 적이 있다면 먼저 확인하세요**
>
> 같은 백엔드 폴더에서 `Test-Path .\venv`를 실행합니다. `False`라면 이 박스를 건너뛰고 아래 생성 명령을 실행합니다.
> `True`라면 `& .\venv\Scripts\python.exe --version`으로 기존 환경의 버전을 확인합니다.
>
> - `Python 3.12.x`라면 생성 명령을 생략하고 (3)부터 이어갑니다.
> - 3.15처럼 다른 버전이면, 새로 연 이 PowerShell에서 아래 명령으로 기존 폴더를 보관한 뒤 생성 명령을 실행합니다.
>   `venv-before-python312`가 이미 있다면 사용하지 않은 다른 보관 이름을 지정하세요.
>
> ```powershell
> Rename-Item -LiteralPath .\venv -NewName venv-before-python312
> ```
>
> 기존 환경의 Python 실행 파일이 없거나 보관 명령에 오류가 나면 생성 명령을 실행하지 말고
> [6장의 가상환경 오류 진단](../06_chapter6.md#ch6-verify-venv)부터 확인합니다.

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

![가상환경 활성화 터미널 예시](../images2/11_chapter11_venv_terminal.png)

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

> [!NOTE]
> **`pymanager` 명령을 찾을 수 없다면**
>
> Python과 Python Install Manager는 별개입니다. 3.15가 실행돼도 Manager 명령이 없을 수 있습니다.
> [6장의 Python Install Manager 설치 안내](../06_chapter6.md#ch6-python-ready)에 따라 Manager를 설치하고,
> 새 PowerShell을 열어 위의 백엔드 폴더 이동부터 다시 실행합니다.

> [!NOTE]
> **조직 정책 때문에 활성화가 계속 차단된다면**
>
> (4)의 두 명령에서 `python` 대신 `& .\venv\Scripts\python.exe`를 사용해 버전과 경로를 확인합니다.
> 확인 결과가 맞으면 (5)에서도 아래 명령으로 가상환경의 Python을 직접 지정합니다.
>
> ```powershell
> & .\venv\Scripts\python.exe -m pip install -r requirements.txt
> ```
>
> 이 경우 (5)의 일반 `python` 명령은 실행하지 않습니다. 이후 이 장에서 Python 경로를 직접 지정하는 명령은 그대로 사용할 수 있습니다.

> [!NOTE]
> **[막혔을 때] PyYAML 빌드 오류가 나온다면**
>
> `Building wheel for pyyaml ... error`와 `Microsoft Visual C++ 14.0 or greater is required`가 함께 나오면,
> PyYAML을 내 PC에서 빌드하려다 컴파일러가 없어 실패한 것입니다. 먼저 (4)의 실제 Python 버전과 경로를 다시 확인합니다.
> 다른 버전의 가상환경을 사용했다면 (2)의 기존 환경 확인 박스부터 진행하세요.
> Python 3.12와 경로가 모두 맞다면 환경을 다시 만들거나 의존성 파일을 바꾸기 전에
> 오류 메시지와 네트워크 상태를 확인하고 [6장의 가상환경 오류 진단](../06_chapter6.md#ch6-verify-venv)을 참고합니다.

> [!NOTE]
> **macOS·Linux에서 진행한다면**
>
> Python 3.12를 준비한 뒤 같은 백엔드 폴더에서 `python3.12 -m venv venv`로 만들고,
> `source venv/bin/activate`로 활성화합니다. (4)에서 버전과 `venv/bin/python` 경로를 확인한 뒤 (5)의 설치 명령을 실행합니다.
> 이후 본문의 `& .\venv\Scripts\python.exe`는 `./venv/bin/python`으로 바꿉니다.
> 기존 가상환경은 버전과 경로를 확인하고 사용하며, Windows의 실행 정책 명령은 실행하지 않습니다.

**여기까지의 완료 기준:** 시작 파일 확인, `npm ci`, Python 3.12 가상환경의 패키지 설치를 모두 마쳤습니다.
잠시 멈춘다면 마지막 완료 단계를 기록하세요. 다음에는 같은 백엔드 폴더에서 기존 가상환경을 사용해 4단계부터 이어갑니다.
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

프로젝트 생성이 제한되면 [공통 부록의 생성 한도 안내](../supplements/supabase_project_setup.md#supabase-project-limit)를 확인합니다.

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

**이 단계 완료:** 오류 없이 결과 표의 `1`을 확인했습니다. SQL Editor의 사용 방법은 [공식 SQL 실행 안내](https://supabase.com/docs/guides/database/functions#getting-started)를 참고하세요.

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

![Connect에서 Session pooler와 URI를 선택한 연결 정보 화면](../images2/11_chapter11_supabase_connect_pooler.png)

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

자세한 형식은 [Supabase 연결 안내](https://supabase.com/docs/guides/database/connecting-to-postgres)와
[SQLAlchemy psycopg2 연결 명세](https://docs.sqlalchemy.org/en/21/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg2)를 참고합니다.
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

**연결에 실패했을 때만 확인하기**

오류 종류만 표시되도록 했으므로 실제 연결 주소나 오류 원문을 채팅에 붙이지 않습니다.

1. `ArgumentError`라면 `.env` 주소의 오타와 `postgresql+psycopg2://` 시작 부분, 주소 전체를 복사했는지 확인합니다.
2. 드라이버 모듈 오류라면 3단계의 가상환경에 의존성이 설치됐는지 확인합니다.
3. `OperationalError`라면 자신의 프로젝트 화면과 호스트·사용자명·포트, 비밀번호 처리와 네트워크 상태를 대조합니다.
4. 프로젝트가 일시 중지됐다면 대시보드에서 해당 Chapter 11 프로젝트를 재개한 뒤 다시 확인합니다.

**첫 명령으로 연결값을 해제하는 이유**

연결 확인의 첫 명령은 이 장에서 서버를 실행할 때마다 반복됩니다. 이유는 한 가지입니다.
`load_dotenv()`는 터미널에 이미 `DATABASE_URL`이 있으면 `.env`의 값으로 덮어쓰지 않습니다.
이전 장에서 같은 이름의 값을 터미널에 설정해 두었다면, `.env`에 Chapter 11 주소를 적어도
다른 프로젝트에 접속할 수 있습니다. 이 명령은 **현재 터미널의 `DATABASE_URL`만 해제**해
항상 `.env`를 쓰게 합니다. 사용자·시스템 전역 설정은 바꾸지 않으며, 새 터미널을 열면 다시 실행합니다.
macOS·Linux에서는 같은 목적으로 `unset DATABASE_URL`을 실행하고, 위 Python 코드를
`./venv/bin/python`으로 실행합니다.



### 6단계. 실습 동작 최종 체크리스트

- [ ] `npm ci`와 가상환경의 `pip install`이 성공했다.
- [ ] 3단계에서 백엔드 `venv`의 Python 실행 경로를 확인했고, `.env`에 자신의 연결값을 입력했다.
- [ ] 전용 실습 DB에서 표식 SQL을 실행했다.
- [ ] 5단계의 연결 확인에서 `1`이 출력됐다.
- [ ] 두 서버의 포트 `8000`·`5173`을 사용할 수 있고 Supabase 프로젝트가 활성 상태다.

**환경 준비 완료:** 위 항목을 모두 확인했다면 [본문 11.1로 돌아갑니다](../11_chapter11.md#ch11-after-environment). 이 장에서 설치와 연결 설정이
가장 번거로운 구간이 끝났습니다. 지금부터는 SQL 실행, Swagger 요청, 브라우저 화면처럼 결과가 눈에 바로 보이는
실습입니다. 연결 확인의 `1`은 DB와 통신했다는 뜻입니다.
주문 테이블·승인 함수는 아직 없는 것이 정상이며, 11.2에서 만들어 첫 승인 결과를 확인합니다.


### 중단 후 다시 시작할 때

<a id="ch11-resume"></a>

1. VS Code에서 기존 `practice-workspace/ch11/`을 열고, 관찰 기록과 마지막으로 진행한 절을 확인합니다.
   완료한 설치·생성 SQL은 반복하지 않습니다. 아직 테이블을 만들지 않았다면 11.2의 미완료 작업부터 이어갑니다.
2. 해당 단계에 필요한 서버 중 꺼진 것만 [백엔드](../11_chapter11.md#ch11-api-run)·[프론트엔드](../11_chapter11.md#ch11-ui-run) 안내로 켭니다.
   백엔드는 안내대로 현재 터미널의 `DATABASE_URL`을 해제하고 기존 `venv`의 Python으로 실행합니다.
   Supabase 프로젝트가 일시 중지됐다면 대시보드에서 재개하고 [연결 확인](#ch11-db-check)을 합니다.
3. 이어갈 절의 **시작 상태**와 현재 DB 값을 대조합니다. 이미 성공한 단계는 기록을 확인하고 다음 단계로 갑니다.
   다음 정상 승인 실험은 관찰값을 보존한 뒤 [초기화 SQL](../11_chapter11.md#reset-sql)로 `CREATED·10·0`을 준비합니다.

재고 부족 오류 화면이 남아 있다면 [재고 복원과 재시도](../11_chapter11.md#ch11-check-retry)부터 이어갑니다.
화면이 사라졌다면 [재고 부족 실험](../11_chapter11.md#ch11-check-shortage)부터 다시 준비합니다.
재시도까지 성공했다면 추가 초기화 없이 [AI 코드 안내](../11_chapter11.md#ch11-ai-review)로 갑니다.

11.2의 중간 실패 실험에서 멈췄다면 [임시 제약 제거](../11_chapter11.md#ch11-db-atomicity)부터 확인합니다.
제약을 남긴 채 API 실습으로 넘어가지 않습니다.

응답 결과를 모르거나 기록과 DB 값이 다르면 초기화·재요청 전에 현재 상태부터 확인합니다.
원인이 불분명하면 [AI 원인 조사](../11_chapter11.md#ch11-ai-debug)를 사용합니다.

<a id="ch11-experiment-states"></a>

**11.6의 상태 변화 지도**

```mermaid
flowchart TD
    A["정상 승인: 11.5 기록 사용·재요청 없음<br/>CREATED·10·0 → PAID·7·1<br/>화면: 완료·버튼 잠금"]
    B["재고 부족: CREATED·2·0에서 요청<br/>400 뒤 DB 그대로<br/>화면: 오류"]
    C["재고 복원 뒤 같은 화면에서 한 번 요청<br/>200 뒤 PAID·7·1<br/>화면: 완료·AI 검토로 이동"]
    A -->|"DB 초기화·재고 2로 변경·새로고침"| B
    B -->|"DB만 초기화·오류 화면 유지·새로고침하지 않음"| C
```

<a id="ch11-run-help"></a>

### 실행 오류 도움말

문제가 생긴 단계만 확인합니다. 원인이 불분명하면 아래 AI 원인 조사를 사용합니다.

<a id="ch11-ai-debug-help"></a>

**AI와 원인 좁히기**

현재 단계와 실제 증상을 한 문장 덧붙여 아래 요청을 보냅니다. 비밀값이 섞인 오류 전문은 붙여 넣지 않습니다.

> **[AI 원인 조사 프롬프트]**
>
> ```text
> Chapter 11의 AGENTS.md와 관련 코드, 보존한 SQL 실행본, 관찰 기록을 읽고 원인만 조사해 주세요. 아직 수정하지 마세요.
> 제가 관찰한 증상에서 예상과 실제 결과가 어디서 달라졌는지 찾아 주세요.
> 확인된 사실과 원인 후보를 실제 코드 위치와 함께 설명하고, 원인을 좁힐 다음 확인 한 가지를 알려 주세요.
> ```

AI가 안내한 코드와 실제 결과를 대조합니다. 원인이 확인되면 수정할 부분과 이유를 확인하고 해당 단계의 수정을 요청합니다.
바뀐 부분의 실험을 다시 하며, SQL을 다시 적용했다면 성공한 실행본도 다음 번호로 보존합니다.

**DB 생성·등록**

> 외래 키는 다른 테이블의 값을 참조하는 연결입니다. 참조 오류가 나면
> 부모인 `stock`이 먼저 생성됐는지 확인하세요. 고정 데이터 등록에서 중복 키 오류가 나면 같은 ID의 데이터가 이미 있는지,
> 생성 SQL에 샘플 INSERT가 포함됐거나 등록 명령을 다시 실행했는지 확인합니다. 이미 만든 테이블이나 고정 데이터를 다시 등록하지 말고,
> 현재 상태와 실패 위치를 [AI 원인 조사 프롬프트](#ch11-ai-debug-help)로 좁힙니다. 생성 순서나 중복 등록이 원인인지 확인한 뒤
> 필요한 부분만 [참조 SQL](../11_chapter11.md#ch11-db-reference)과 비교합니다.

**API 실행·연결**

> `No module named 'api'`가 나오면 현재 폴더가 `erp-project/`인지,
> 기존 `venv`의 Python을 사용했는지, `api/main.py`가 있는지(`Test-Path api/main.py`)를 차례로 확인합니다.
> `400`의 `detail`에 연결 오류가 보이면 [환경 준비의 연결 확인](ch11_environment_setup.md#ch11-db-check)부터 다시 실행합니다.
> 패키지 설치 오류는 [가상환경·설치 안내](ch11_environment_setup.md#ch11-python-setup)로 돌아가 확인합니다.
> API 동작이 다르면 요청과 응답을 기록하고 [AI 원인 조사 프롬프트](#ch11-ai-debug-help)로 입력 검사·DB 호출·응답 중 어디서 달라졌는지 좁힙니다.
> 원인이 확인된 부분만 [참조 API](../11_chapter11.md#ch11-api-reference)와 비교합니다.
> 연결값은 AI에 전달하지 않습니다.

**화면 요청·상태**

>
>
> - 화면의 요청 오류는 Network에서 실제 주소·본문·응답부터 확인합니다. CORS 오류는 현재 페이지가
>   API에서 허용한 `http://localhost:5173`인지, 404는 요청 주소가 맞는지, 422는 오류 필드가 무엇인지 확인합니다.
> - 로딩이 멈췄다면 요청이 아직 `Pending`인지 먼저 봅니다. 참조 코드에는 요청 제한 시간이 없어 응답 전에는
>   `finally`에 도달하지 않습니다. 결과를 모르는 요청은 반복 전송하지 말고 DB 상태부터 조회합니다.
> - 응답이 끝났는데 화면 상태가 다르면 [AI 원인 조사 프롬프트](#ch11-ai-debug-help)를 사용합니다. 예를 들어 “응답 200인데 완료 표시가 없다”는 증상에는
>   AI가 실제 응답 본문과 성공 판정 조건, 완료 상태와 화면 표시의 연결을 차례로 대조하게 합니다.
>   원인이 확인된 부분만 [참조 코드](../11_chapter11.md#ch11-ui-state-reference)와 비교하고, 최소 수정 뒤 관련 실험을 다시 수행합니다.

[본문으로 돌아가기: 11.1 업무회의](../11_chapter11.md#ch11-after-environment)
