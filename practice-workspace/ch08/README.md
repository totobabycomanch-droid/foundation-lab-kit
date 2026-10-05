# Chapter 8 — 요청 해석·업무 판단·저장·HTTP 연결로 나누어 만드는 발주 API

이 폴더는 8장의 발주 실습용 시작 키트입니다. 완성 코드는 포함하지 않습니다.
합본 원고의 8.1~8.6 순서로 같은 `project/`를 이어서 사용합니다.
8.2~8.3에서 요청 해석과 업무 판단을 만들고, 같은 폴더에서 8.4의 저장과
8.5의 HTTP 연결을 이어갑니다.

키트의 검증·초기화 도구는 Windows PowerShell용 `.ps1` 파일입니다. Python·pytest 코드는 다른
운영체제에서도 실행할 수 있지만, 이 README의 키트 관리 명령은 Windows 환경을 기준으로 합니다.

## 시작 위치

VS Code에서 이 `ch08` 폴더를 엽니다. 다른 장의 코드나 `reference-app`을 복사하지 않습니다.
`AGENTS.md`와 `project/AGENTS.md`를 확인하고, 구현은 `project/` 안에서만 진행합니다.
`project/AGENTS.md`의 교육용 파일 위치·공개 규약을 조사 기준으로 사용합니다.
이는 원고의 import·실행 명령을 연결하기 위한 규약이며, 내부 구현 방식까지 고정하지 않습니다.
이 장은 이전 장의 환경을 재사용하지 않고 `ch08/.venv`를 사용합니다. `ch08` 폴더에서 기존
가상환경을 확인하고, 없으면 Python 3.12로 생성합니다.

```powershell
Test-Path .\.venv\Scripts\python.exe
```

결과가 `False`일 때만 자신의 Python 설치 방식에 맞는 명령 하나를 실행합니다.

```powershell
pymanager exec -V:3.12 -m venv .venv
# 또는 python --version이 Python 3.12.x인 경우
python -m venv .venv
```

생성 결과를 확인하고 같은 PowerShell에서 활성화한 뒤 의존성을 설치합니다.

```powershell
Test-Path .\.venv\Scripts\python.exe
& .\.venv\Scripts\python.exe --version
& .\.venv\Scripts\Activate.ps1
Set-Location project
python -m pip install -r requirements.txt
python -c "import sys; print(sys.executable)"
```

마지막 경로가 `ch08\.venv\Scripts\python.exe`로 끝나야 합니다. 활성화가 실행 정책 때문에
차단되면 정책을 바꾸지 말고 VS Code 인터프리터로 해당 Python을 선택해 새 터미널을 열거나,
`ch08` 폴더에서 다음 명령으로 의존성을 설치합니다.

```powershell
& .\.venv\Scripts\python.exe -m pip install -r .\project\requirements.txt
```

이후 Python·pytest 명령은 `ch08/.venv`를 사용하는 PowerShell의 `project/`에서 실행합니다.
기존 `database.py`, `models.py`, `practice_db.py`, `.env.example`, `_starter/`는 시작 파일입니다.
`services/`, `repositories/`, `routers/`, `tests/`의 `__init__.py`도 이미 제공됩니다.
`.env`와 비밀번호·키·실제 DB URL을 AI에게 읽히거나 출력하지 않습니다.

## AI와 진행하는 순서

1. 원고의 현재 단계 프롬프트 블록 하나를 전달합니다. AI는 상위·현재 폴더·project 지침과 README를 조사합니다.
2. AI의 보고를 결과물·파일 위치·보존 파일·검증 방법과 대조한 뒤 범위를 승인합니다.
   같은 세션에서 이미 승인한 범위는 이어서 진행하며 변경 범위가 달라지면 다시 확인합니다.
3. 생성된 코드를 직접 열고 실행한 뒤 해당 단계의 검증 블록 하나를 전달합니다.
4. AI 판정과 직접 실행한 결과를 비교합니다. 계산 테스트, 앱 등록과 실제 발주 결과를 확인하면
   Core가 끝납니다. 별도 기록 파일은 필수가 아닙니다.

## 실습 경로

| 단계 | 만드는 것 | 확인할 것 |
|---|---|---|
| 8.2 요청 해석 | services/franchise_order.py, tests/test_change.py | 정상 요청 생성·잘못된 값 거부·공백 제거·값 변경 불가 (DB 없음) |
| 8.3 업무 판단 | services/franchise_order.py에 판단 추가, tests/test_change.py에 판단 사례 추가 | 기존 요청 검증을 보존하고 정상 판단·재고 부족·예치금 부족·정확한 경계값 확인 (DB 없음) |
| 8.4 저장 | repositories/franchise_order.py, tests/test_persist.py | 한 트랜잭션 저장과 실패 시 전체 취소 (인메모리 SQLite) |
| 8.5 HTTP 연결 | routers/franchise_order.py, main.py | 조회·판단·저장 호출 순서, 오류의 HTTP 변환, 앱 등록 |
| 8.5 마무리 | 키트의 practice_db.py | 로컬 SQLite 준비·조회와 발주 한 건 실제 처리(재고 95·예치금 45000·주문 1건) |
| Core 완료 | 기존 결과 확인 | 판단·저장 테스트, 앱 등록, 실제 발주 결과 확인 |
| 8.6 선택 | 원고의 선택 실습 | 오류 응답 확인과 심화 주제 |

필수 경로에는 Docker나 DB 서버가 필요하지 않습니다. 로컬 SQLite 파일 DB(`project/chapter8.db`)만
사용합니다. 위 파일은 원고의 해당 단계에서 생성하므로 시작 키트에서 찾을 수 없어도 정상입니다.
요청 해석·업무 판단 완료 후 초기화하지 않습니다. Core는 앱 등록 뒤 로컬 SQLite에서 실제 발주를
실행합니다.

실제 발주 전후의 DB 값은 `project/`에서 다음 두 명령으로 준비하고 확인합니다.

```powershell
python practice_db.py prepare
python practice_db.py show
```

## 선택 DB·HTTP 실습

8.4의 `tests/test_persist.py`는 인메모리 SQLite로 자체 DB를 만들고 정리합니다. 오류 응답 확인은 8.5 마무리에서 만든
`chapter8.db`와 서버를 이어서 사용합니다. 기존 데이터가 있다면 정상 예시의 초기값을 가정하지 않습니다.
원격 PostgreSQL은 별도 연결·드라이버가 필요한 선택 경로이며 운영·공용 DB에서 실습하지 않습니다.

## 시작 파일 확인과 복습

키트 루트인 `foundation-lab-kit`에서 다음 명령을 실행합니다.

```powershell
./tools/verify_practice_chapter.ps1 -Chapter ch08
./tools/reset_practice_chapter.ps1 -Chapter ch08
```

두 번째 명령은 초기화 대상 미리 보기입니다. 필요한 코드와 기록을 보관하고 원고의 초기화
절차를 확인한 뒤에만 적용합니다. `_starter/`를 직접 수정하지 않습니다.
