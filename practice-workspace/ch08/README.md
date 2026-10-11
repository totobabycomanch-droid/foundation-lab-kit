# Chapter 8 — 요청 검증·업무 판단·저장·API 연결로 나누어 만드는 발주 API

이 폴더는 8장의 발주 실습용 시작 키트입니다. 완성 코드는 포함하지 않습니다.
합본 원고의 8.1~8.6 순서로 같은 `project/`를 이어서 사용합니다.
8.2~8.3에서 요청 검증과 업무 판단을 만들고, 같은 폴더에서 8.4의 저장과
8.5의 API 연결을 이어갑니다.

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

## AI 공통 지침

`ch08/AGENTS.md` 옆에 공통 지침 두 파일과 업무 명세가 제공됩니다. 독자가 새로 작성하지 않습니다.

- `ai_build_rules.md`: 각 단계 생성 요청의 조사·계획·승인·구현·테스트 지침
- `ai_review_rules.md`: 생성 후 결과 보고와 마지막 통합 리뷰의 근거·판정 기준
- `chapter8_order_spec.md`: 네 단계의 입력·업무 규칙·저장 조건과 필수 검사

반복 작업 지시는 공통 지침에, 발주 조건은 업무 명세에 있습니다. 공개 이름과 구현 위치는
`project/AGENTS.md`에서 확인합니다. 새 AI 세션에서도 요청에서 지침과 명세의 해당 단계를
읽도록 지정하고, 이전 결과는 실제 구현에서 조사합니다.

v1.3.10에는 지침 두 파일과 업무 명세가 모두 포함됩니다. 보충 ZIP을 따로 적용하지 않습니다.
처음 실습할 때는 새 폴더에 키트를 풀고 Python 환경을 준비하세요. 이전 실습 코드·DB·가상환경은
가져오지 않습니다. 이미 v1.3.9로 진행 중이라면 기존 결과를 보존하며 문서·도구만 갱신할 수 있습니다.

## AI와 진행하는 순서

1. 원고의 현재 단계 프롬프트 블록 하나를 전달합니다. AI는 지침·README·업무 명세와 기존 구현을 조사합니다.
2. AI의 보고를 결과물·파일 위치·보존 파일·검증 방법과 대조한 뒤 범위를 승인합니다.
   같은 세션에서 이미 승인한 범위는 이어서 진행하며 변경 범위가 달라지면 다시 확인합니다.
3. AI의 구현·테스트 완료 보고를 받은 뒤 원고의 명령을 직접 실행하고 대표 결과를 확인합니다.
4. 네 기능을 연결한 뒤 실제 HTTP·DB 결과와 함께 통합 리뷰를 한 번 요청합니다.
   별도 기록 파일은 필수가 아닙니다.

## 실습 경로

| 단계 | 만드는 것 | 확인할 것 |
|---|---|---|
| 8.2 요청 검증 | services/franchise_order.py, tests/test_change.py | 최소 마스터·상세 생성, 잘못된 값·중복 거부, 서버 소유 값 폐기, 불변 객체(DB 없음) |
| 8.3 업무 판단 | services/franchise_order.py에 판단 추가, tests/test_change.py에 판단 사례 추가 | 서버 상품 단가로 공급가액·VAT·합계 계산, 상품 없음·비활성·잘못된 단가 확인(DB 없음) |
| 8.4 저장 | repositories/franchise_order.py, tests/test_persist.py | 마스터·상세·감사 1·1·1 저장과 상세·감사 실패 시 0·0·0 롤백(인메모리 SQLite) |
| 8.5 API 연결 | routers/franchise_order.py, main.py, tests/test_api.py | 조회·판단·단일 저장 호출, 200·400·409·500 변환, 앱 등록 |
| 8.5 마무리 | 키트의 practice_db.py | 상품 준비·조회와 발주 한 건 실제 처리(단가 1000 유지·마스터/상세/감사 1·1·1·합계 5500) |
| Core 완료 | `tools/verify_ch08_core.ps1` | 세 테스트, 고정 계약, 앱 등록, 실제 발주 결과의 DB 값을 한 번에 확인 |
| 8.6 선택 | 원고의 선택 실습 | 오류 응답 확인과 심화 주제 |

필수 경로에는 Docker나 DB 서버가 필요하지 않습니다. 로컬 SQLite 파일 DB(`project/chapter8.db`)만
사용합니다. 위 파일은 원고의 해당 단계에서 생성하므로 시작 키트에서 찾을 수 없어도 정상입니다.
요청 검증·업무 판단 완료 후 초기화하지 않습니다. Core는 앱 등록 뒤 로컬 SQLite에서 실제 발주를
실행합니다. 발주 마스터·상세·감사만 저장하고 상품 단가와 활성 상태는 그대로 유지합니다.
이번 실습에 없는 모델·업무 규칙은 추가하지 않습니다.

실제 발주 전후의 DB 값은 `project/`에서 다음 두 명령으로 준비하고 확인합니다.

```powershell
python practice_db.py prepare
python practice_db.py show
```

Core의 실제 HTTP 확인은 정상 200과 수량 0의 400, 요청 뒤 DB 결과까지입니다. 단가 0의 409는
자동 테스트에 유지하고, 실제 상품 단가 변경·복구와 HTTP 409 확인은 선택 실습으로 진행합니다.

## 선택 DB·HTTP 실습

8.4의 `tests/test_persist.py`는 인메모리 SQLite로 자체 DB를 만들고 정리합니다. 오류 응답 확인은 8.5 마무리에서 만든
`chapter8.db`와 서버를 이어서 사용합니다. 기존 발주 데이터가 있다면 1·1·1건이라는 정상 예시 결과를
가정하지 않습니다.
원격 PostgreSQL은 별도 연결·드라이버가 필요한 선택 경로이며 운영·공용 DB에서 실습하지 않습니다.

## 시작 파일 확인과 복습

키트 루트인 `foundation-lab-kit`에서 다음 명령을 실행합니다.

```powershell
./tools/verify_practice_chapter.ps1 -Chapter ch08
./tools/reset_practice_chapter.ps1 -Chapter ch08
```

Core를 마친 뒤 같은 위치에서 `./tools/verify_ch08_core.ps1`을 실행하면 세 테스트 파일, 앱 등록과
`chapter8.db` 값(상품 단가 1000·활성 유지, 마스터·상세·감사 1·1·1건, 합계 5500)을 읽기 전용으로
확인합니다. 이 도구는 실제 HTTP 요청을 보내지 않으므로 HTTP 실행 결과는 별도로 확인합니다.

두 번째 명령은 초기화 대상 미리 보기입니다. 필요한 코드와 기록을 보관하고 원고의 초기화
절차를 확인한 뒤에만 적용합니다. `_starter/`를 직접 수정하지 않습니다.
