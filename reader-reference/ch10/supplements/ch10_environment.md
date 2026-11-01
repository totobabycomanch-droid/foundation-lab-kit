# Chapter 10 환경·복구 도움말

[10장 Core로 돌아가기](../README.md#return-to-book)

DB 준비 단계에서 Supabase를 처음 사용한다면 [공통 부록의 전용 프로젝트 준비](supabase_project_setup.md)를 확인합니다.
Python 서버만 먼저 확인할 때는 DB가 필요하지 않습니다. 본문 Step 2의 `/health`부터 확인하세요.

기본 실행은 가상환경이 활성화된 `erp-mini` 터미널에서 `python -m uvicorn lab_app:app --host 127.0.0.1 --port 8310 --reload`입니다.
연결 오류는 503, 시작 주문 업무의 미구현은 501, 의도적 저장 오류는 500으로 구분합니다.
일반 입력 오류의 422는 중간 롤백 실험이 아닙니다. 화면의 실행 결과 복사를 기본 경로로 사용합니다.

<a id="ch10-help-index"></a>

**증상별로 찾아가기**

오류가 난 단계에서 멈추고 아래 표의 해당 항목만 확인합니다. 해결한 뒤에는 완료한 작업을 처음부터 반복하지 않고 마지막 열의 확인으로 돌아갑니다.

| 증상 | 확인할 안내 | 해결 후 확인 |
|---|---|---|
| 키트 검사에서 `FAIL` | [본문의 파일 준비](../README.md#return-to-book). 압축을 푼 위치와 표시된 누락 파일 확인 | 파일 검사 마지막에 `ch10 static verification passed.` 표시 |
| 가상환경 활성화·스크립트 실행 차단 | [실행 정책](#ch10-execution-policy) | `(.venv)` 표시 또는 `.venv`의 Python 직접 실행 확인. 재개 중이면 아래 재개 표로 복귀 |
| `python`을 찾을 수 없음·가상환경 파일이 없음 | [패키지 설치](#ch10-install-help) | Python 실행과 `erp-mini/.venv` 생성 확인 후 실패한 명령부터 재개 |
| 설치 실패·`No module named ...` | [패키지 설치](#ch10-install-help) | 설치 명령 오류 해소와 `pip check` 확인 후 Step 2의 `/health` 응답 확인 |
| 8310 포트 사용 중 | [서버 오류](#ch10-runtime-help)의 포트 안내 | 선택한 포트의 `/health`에서 `{"status":"ok"}` 확인 |
| `DB connection OK`가 나오지 않음 | [연결·인증 오류](#ch10-runtime-help) | Step 3의 연결 확인 명령 성공 |
| 서버는 켜지지만 화면에 503 | [연결·표식·스키마 확인](#ch10-runtime-help) | 현재 DB 결과 조회 성공. 재개 중이면 기존 주문·가격부터 확인 |
| 주문 버튼에서 501 | [주문 미구현 확인](#ch10-order-unimplemented) | 구현·검사를 마친 뒤 Step 5에서 화면 조회. 기초 데이터 SQL 재실행은 불필요 |
| 중단 후 재개·예시와 다른 재고 | [재개 표](#ch10-resume) | 마지막 완료 실험 다음부터 진행. 주문·초기화 반복 금지 |
| 정상 주문을 실수로 더 보냄 | [중복 주문 후 이어가기](#ch10-extra-order) | 추가 주문 기록을 보존하고 자신의 전후값으로 비교 |
| DB 결과가 미확인 | [조회 미확인](#ch10-observation-help) | 최신 조회와 실패 직전 기록 비교. 미확인 상태로 완료 판정하지 않음 |
| 실행 결과 자동 복사 실패 | [직접 복사](#ch10-copy-help) | 실행 결과 텍스트를 보관하고 Step 9에 전달 |

<a id="ch10-resume"></a>

## 중단 후 실습 재개

처음 진행하는 독자는 [본문](../README.md#return-to-book)으로 돌아가 Step 1부터 순서대로 진행합니다. 서버를 종료해도 DB의 주문은 남습니다.
멈추기 전에는 마지막 완료 Step·주문번호·관찰값·다음 행동을 기록합니다. 화면 실험을 했다면 실행 결과도 복사해 보관하세요.
새로고침하면 이 탭에서 모은 복사 기록은 새로 시작합니다. 연결 문자열과 비밀번호는 기록하지 않습니다.

다시 시작할 때는 다음 순서로 확인합니다.

1. 기존 `ch10/` 폴더를 VS Code에서 엽니다. 가상환경을 이미 만들었다면 [기존 가상환경 활성화](#ch10-reactivate)만 따릅니다.
2. DB 준비까지 마쳤다면 [Step 3의 연결 확인](../README.md#return-to-book)만 실행합니다. `schema.sql`과 `10_seed.sql`은 다시 실행하지 않습니다.
3. 주문 코드를 구현했다면 [Step 5](../README.md#return-to-book)에서 서버를 실행하고 현재 DB 결과를 먼저 조회합니다. 주문 버튼은 아직 누르지 않습니다.
4. 아래 표에서 마지막으로 확인한 결과에 맞춰 이어갑니다.

| 마지막으로 확인한 결과 | 이어갈 위치와 행동 |
|---|---|
| 환경 준비 중 오류로 중단 | Step 2 또는 Step 3에서 실패한 명령·준비 작업부터 해결. 완료한 설치·SQL은 반복하지 않음 |
| Step 2의 서버 응답 확인 | Step 3의 전용 DB 준비부터 진행 |
| Step 3의 DB·기초 데이터 준비 완료 | Step 4에서 현재 구현 상태 조사. 기존 코드를 시작본으로 덮어쓰지 않음 |
| Step 4의 구현 완료 | Step 5에서 서버 실행과 현재 재고·가격 조회 |
| Step 6의 정상 주문 확인 | 기존 주문번호와 관찰 기록을 보존하고 Step 7의 가격 비교로 진행. 정상 주문은 다시 보내지 않음 |
| Step 7의 가격 비교 완료 | 현재가 5000과 기존·신규 주문 단가 5000·6000을 확인하고 Step 8의 롤백 검증으로 진행 |
| Step 8의 실패 전후 보존 확인 | Step 9에서 보관한 실행 결과로 검증 |

Step 7의 가격 6000에서 중단했다면 현재 가격과 주문 단가를 먼저 읽습니다. 6000으로 저장된 새 주문이 이미 있다면 재주문하지 않고 현재 가격만 5000으로 되돌려 비교합니다.
기록이 부족해 실패 전후를 비교할 수 없다면 완료로 판정하지 않습니다. 현재값으로 과거 결과를 추정하거나 주문을 반복하지 말고, Step 9에서 필요한 재검증을 AI와 정합니다. 보관한 실행 결과가 있다면 그 기록을 그대로 전달합니다.
처음 상태로 되돌려야 할 때만 [초기화 도움말](#ch10-reset)을 사용합니다. 가격 원복과 주문 삭제는 서로 다른 작업입니다.


<a id="ch10-extra-order"></a>

## 정상 주문을 실수로 더 보냈을 때

정상 주문 버튼은 누를 때마다 새 주문을 저장하고 재고를 차감합니다. 서버 재시작이나 새로고침으로 그 주문이 없어지지는 않습니다.
추가로 주문하거나 `schema.sql`·초기화 SQL을 실행하지 말고 다음 순서로 확인합니다.

1. 화면의 현재 주문번호·품목별 수량과 단가·기록 건수·재고를 확인합니다. 남아 있는 실행 결과는 새로고침 전에 복사해 보관합니다.
2. 언제 어떤 주문을 더 보냈는지 기록합니다. 본문의 예시 수치와 맞지 않더라도 기존 주문을 삭제해 맞추지 않습니다.
3. 추가 주문과 현재값을 확인할 수 있다면 그 값을 기준으로 남은 실험을 진행합니다. 가격 비교에서는 실제 주문번호로 변경 전후의 주문을 구분하고, 실패 실험에서는 자신의 실패 직전·직후 건수와 재고가 같은지 비교합니다.
4. Step 9에서 추가 주문 사실과 자신의 관찰값을 AI에게 함께 전달합니다. 실행 기록이 부족해 확인할 수 없는 항목은 Not Run으로 남기고 필요한 재검증을 정합니다.

예를 들어 새 DB에서 Step 6의 신라면2·코카콜라1 주문만 두 번 성공시켰다면 다음처럼 읽습니다. 다른 조작도 했다면 이 표를 적용하지 말고 자신의 기록을 확인합니다.

| 시점 | 신라면·코카콜라 재고 | 주문·상세·원장·이벤트·초기 이력 건수 |
|---|---|---|
| 정상 주문을 두 번 보낸 직후 | 96·98 | 2·4·7·2·2 |
| 이후 Step 7의 신라면1 새 주문과 가격 원복 완료 | 95·98 | 3·5·8·3·3 |
| 이어서 Step 8의 실패 실험 완료 | 95·98로 유지 | 3·5·8·3·3으로 유지 |

이 경우에도 앞의 두 주문은 단가 5000, 가격 변경 후 새 주문은 6000을 유지해야 합니다. 실패 실험에서는 세 성공 주문이 보존돼야 합니다.
본문의 예시 수치로 처음부터 다시 확인하려는 경우에만 코드·관찰 기록을 보관한 뒤 [초기화 안내](#ch10-reset)를 따릅니다. 초기화는 이미 저장한 실습 결과를 지우는 별도 선택입니다.

<a id="ch10-reactivate"></a>

> **[재개하는 독자만] 기존 환경에서 실습 재개**
>
> 이 안내는 가상환경을 이미 만든 독자를 위한 것입니다. 처음 준비는 본문 Step 2를 따릅니다.
>
> 새 터미널이 `ch10`에서 열렸다면 다음을 한 줄씩 실행합니다. 이미 `erp-mini`라면 첫 줄은 건너뜁니다.
>
> ```powershell
> cd .\erp-mini
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\.venv\Scripts\Activate.ps1
> ```
>
> `Set-ExecutionPolicy`의 확인 질문이 나오면 `Y`를 입력합니다. 설정은 현재 터미널에만 적용됩니다.
> `erp-mini` 터미널 앞에 이미 `(.venv)`가 보이면 위 명령은 실행하지 않습니다.
> 가상환경 생성과 패키지 설치를 반복하지 않습니다. 활성화한 뒤 [재개 표](#ch10-resume)에서 중단했던 위치로 돌아갑니다. 이미 마친 서버 확인도 반복할 필요는 없습니다.

활성화가 실행 정책 오류로 막히면 [실행 정책 도움말](#ch10-execution-policy)을 확인하세요.
macOS/Linux에서는 Python 3.12를 준비하고 `python3.12 -m venv .venv`로 생성합니다. `source .venv/bin/activate`로 활성화한 뒤 `python --version`이 `Python 3.12.x`인지 확인하고, 이후 명령은 동일하게 `python`으로 실행합니다.

<a id="ch10-order-unimplemented"></a>

## 주문 버튼에서 501이 나올 때

HTTP 501은 주문 저장 기능이 아직 미구현 상태로 응답한 것입니다. Step 4의 AI 대화로 돌아가 다음과 같이 요청하세요.

> **HTTP 501이 나올 때 — 주문 저장 코드 확인 요청**
>
> ```text
> 주문 버튼을 누르면 HTTP 501이 나옵니다.
> 현재 실행 중인 프로젝트의 주문 저장 코드가 구현되어 파일에 저장됐는지 확인하고,
> 구현된 코드로 서버가 실행되도록 필요한 조치를 안내해 주세요.
> 제공 화면·DB 연결·스키마·검사는 변경하지 마세요.
> ```

501 원인을 해결한 뒤 본문 Step 6으로 돌아갑니다. 새로 준비한 DB에서 첫 정상 주문을 한 번 보내 HTTP 200과 기대값을 확인합니다.

<a id="ch10-observation-help"></a>

## DB 조회가 미확인일 때

> **DB 조회가 ‘미확인’으로 표시될 때**
>
> 화면에 **‘아래 표는 이전 조회값입니다’**라는 안내가 나오면, 보이는 숫자는 이번 실패 요청 이후의 결과가 아닐 수 있습니다.
>
> 1. 주문 버튼을 다시 누르지 말고 **DB 결과 다시 조회**를 누르세요.
> 2. 조회가 성공하면 **실제 DB 저장 결과**의 기록 건수·재고·주문 상세를 실패 직전 값과 비교하세요.
> 3. 계속 조회되지 않거나 실패 직전 값을 확인할 수 없다면, 완료로 판정하지 말고 화면의 실행 결과를 복사해 Step 9의 AI 검증에 전달하세요.

여기서는 SQL Editor에서 SELECT를 실행할 필요가 없습니다. **DB 결과 다시 조회**는 현재 DB 표를 갱신하지만,
**이번 주문 요청의 전후 비교**를 다시 만들지는 않습니다. 그 영역에 남은 ‘미확인’ 표시가 해소됐다고 판단하지 마세요.

<a id="ch10-copy-help"></a>

## 실행 결과 복사와 대체 서버 실행

자동 복사가 안 되면 **실행 결과 직접 복사**를 열어 Ctrl+C로 복사합니다. 중단하기 전에는 새로고침하거나 창을 닫기 전에 이 결과를 보관합니다.
Step 9를 재개할 때 이미 보관한 기록이 있다면 그 기록을 사용합니다. 새 탭에서 DB를 조회한 결과만으로 이전 실패 전후의 기록을 대신하지 않습니다.

본문 Step 5의 서버 명령 대신 제공 실행 스크립트를 사용하려면 가상환경이 활성화된 `erp-mini` 폴더에서 아래 명령을 실행합니다. 두 실행 방법 중 하나만 사용합니다.

> **선택: 제공 스크립트로 실습 서버 시작**
>
> ```powershell
> powershell -NoProfile -ExecutionPolicy Bypass -File ..\start_lab.ps1
> ```

<a id="ch10-execution-policy"></a>

## PowerShell 스크립트 실행이 차단될 때

‘이 시스템에서 스크립트를 실행할 수 없으므로’라는 오류는 `.ps1` 파일이 실행되기 전에 PowerShell 실행 정책이 차단한 것입니다.
가상환경 활성화 명령인 `.\.venv\Scripts\Activate.ps1`이 차단됐다면 `erp-mini` 터미널에서 다음을 한 줄씩 실행합니다.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

첫 명령은 현재 터미널의 PowerShell 프로세스에만 적용되며, 터미널을 닫으면 효력이 끝납니다.
확인 질문이 나오면 `Y`를 입력합니다. 이 범위의 설정에는 관리자 권한이 필요하지 않습니다.
활성화 후 `(.venv)`가 표시되면 본문의 `python` 명령으로 돌아갑니다.

실습 키트의 검사·실행 스크립트를 실행할 때는 다음 방식을 사용합니다.
이 장의 스크립트는 `powershell -NoProfile -ExecutionPolicy Bypass -File` 뒤에 실행할 파일 경로를 지정합니다.
이 설정은 새로 실행하는 PowerShell 프로세스에만 적용하며, 사용자·시스템의 실행 정책을 영구 변경하지 않습니다.

이 방식으로도 차단된다면 아래 명령으로 정책을 확인합니다.

```powershell
Get-ExecutionPolicy -List
```

`MachinePolicy`나 `UserPolicy`가 설정돼 있다면 조직에서 관리하는 정책일 수 있습니다. 관리 담당자에게 스크립트 실행 허용 여부를 확인합니다.
활성화가 계속 차단되면 `erp-mini`에서 본문의 `python` 대신 `.\.venv\Scripts\python.exe`를 직접 지정해 실행할 수 있습니다.
이 방식에는 `.ps1` 실행 정책이 적용되지 않으므로 `-ExecutionPolicy` 옵션을 붙이지 않습니다.

예를 들어 Step 2의 패키지 설치·점검과 서버 확인은 다음과 같이 실행합니다. 이미 성공한 설치는 반복하지 않습니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m uvicorn lab_app:app --host 127.0.0.1 --port 8310
```

한 줄씩 실행하고 오류가 나면 다음 줄로 넘어가지 않습니다. `/health` 확인 후 Ctrl+C로 서버를 종료합니다.
이 방법에서는 `(.venv)`가 표시되지 않아도 됩니다. 이후에도 본문의 `python` 부분을 `.\.venv\Scripts\python.exe`로 바꿔 실행합니다.

문제가 생겼거나 대체 환경을 선택할 때 필요한 절만 확인합니다. 연결 문자열과 비밀번호를 AI나 로그에 노출하지 않습니다.

<a id="ch10-docker"></a>

## Docker 로컬 PostgreSQL

> **[선택 실습 환경] Docker 로컬 PostgreSQL 준비**
>
> Docker가 준비되어 있다면 로컬 PostgreSQL을 선택할 수도 있습니다. 컨테이너 이미지와 접속 도구는 미리 준비합니다.
>
> 1. **Docker 컨테이너 실행**: 터미널에서 아래 명령으로 로컬 PostgreSQL 16 컨테이너를 기동합니다.
>    ```bash
>    docker run --name erp-postgres -e POSTGRES_PASSWORD=your_password -p 127.0.0.1:5432:5432 -d postgres:16-alpine
>    ```
> 2. **접속 도구 연결**: DBeaver, pgAdmin 등의 데이터베이스 클라이언트에서 `host: localhost`, `port: 5432`, `database: postgres`, `user: postgres`, `password: your_password`로 접속합니다. `select version();`의 결과가 표시되면 연결된 것입니다. 예시 비밀번호를 바꿨다면 접속 도구에도 같은 값을 입력합니다.
> 3. **전용 DB 표식 생성**: 다른 데이터가 없는 Chapter 10 전용 컨테이너인지 확인하고 `erp-mini/sql/00_initialize_lab.sql`을 실행합니다.
> 4. **Core로 진행**: 주문 시스템의 8개 테이블은 10.3 Step 3에서 만듭니다. 별도 SQL 체험은 Core 완료 후 선택합니다.
>
> PC의 5432 포트가 사용 중이면 매핑을 `127.0.0.1:5433:5432`로 바꾸고 접속 도구와 Step 3의
> `.env`에도 포트 5433을 사용합니다. 같은 이름의 컨테이너가 있다면 새 이름으로 생성합니다.
>

---

## SQL 체험 중단 후 복구

<a id="ch10-sandbox-restart"></a>

**체험 중단 후 다시 시작하기**

이 안내는 [선택 SQL 체험](ch10_labs.md#ch10-not-null-lab)을 중단했을 때 사용합니다. 처음 실행할 때는 건너뛰세요.
`relation ... already exists`는 앞서 만든 테이블이 남아 있다는 뜻이고, `duplicate key`는
같은 기본 키의 데이터를 다시 넣었을 때 나타날 수 있습니다. 오류가 나면 뒤의 SQL을 계속 실행하지 않습니다.

1. 현재 접속한 곳이 본문 Step 3에서 준비한 Chapter 10 전용 DB인지 확인합니다.
2. 결과를 이미 확인했다면 해당 체험의 정리 단계만 실행하고 다음 절로 갑니다.
3. 결과를 확인하지 못했거나 어디까지 실행했는지 모르겠다면, 아래에서 **다시 할 체험의 테이블만** 정리합니다.
4. 해당 체험의 준비 단계부터 다시 실행합니다. 조회 결과를 기록한 뒤 마지막에 정리합니다.

| 다시 할 체험 | 정리할 테이블 |
| :--- | :--- |
| 필수값 제약 체험 | `test_orders` |
| 10.4.2 가격 스냅샷 | `temp_sandbox_order_items`, `temp_sandbox_products` |
| 10.4.3 원장 합계 | `temp_sandbox_ledger` |
| 10.4.4 취소·논리 삭제 | `temp_sandbox_orders` |

아래에서 해당하는 줄만 선택해 실행합니다. `IF EXISTS`는 테이블이 이미 없어도 오류를 내지 않게 합니다.
체험 결과를 지우고 다시 시작하는 작업이므로, 보존할 데이터가 없는 체험용 테이블인지 확인하세요.

```sql
DROP TABLE IF EXISTS public.test_orders;
DROP TABLE IF EXISTS public.temp_sandbox_order_items;
DROP TABLE IF EXISTS public.temp_sandbox_products;
DROP TABLE IF EXISTS public.temp_sandbox_ledger;
DROP TABLE IF EXISTS public.temp_sandbox_orders;
```

DB 접속 도구에서 `current transaction is aborted`가 나오면 해당 도구의 롤백 기능으로
실패한 트랜잭션을 취소한 뒤 정리 SQL을 실행합니다. 다른 오류라면 테이블을 임의로 더 지우거나
`CASCADE`를 붙이지 말고, 오류 종류와 대상 이름을 확인합니다.

`temp_sandbox_`는 실제 임시 테이블 기능이 아니라 체험용으로 붙인 이름입니다. 창을 닫거나
Python 서버를 종료해도 남을 수 있습니다. 이 체험을 다시 하려고 주문용 `schema.sql`이나
장 전체의 `99_reset_lab.sql`을 실행할 필요는 없습니다.

---

<a id="ch10-cli-options"></a>

**선택: 명령줄에서 주문 요청하기**

Core는 제공된 실습 화면을 사용합니다. 아래는 같은 정상 주문을 명령줄에서 보내는 대체 방법입니다. 서버는 실행 중이어야 합니다.
서버 터미널은 그대로 두고 요청용 터미널을 하나 더 엽니다. 아래 세 방법 중 사용하는 셸에 맞는 하나만 선택합니다.
이미 정상 주문을 보냈다면 연습 삼아 다시 실행하지 마세요. 새 주문과 재고 차감이 생깁니다.

**주문 요청 테스트 (Linux / macOS - curl, Swagger 대신 선택):**
```bash
# 앞서 Step 3에서 기초 데이터를 입력했다면 아래 curl 명령이 오류 없이 정상 수행됩니다.
curl -X POST http://127.0.0.1:8310/orders \
  -H "Content-Type: application/json" \
  -d '{
    "corp_id": "11111111-1111-1111-1111-111111111111",
    "items": [
      {
        "product_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "quantity": 2
      },
      {
        "product_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "quantity": 1
      }
    ]
  }'
```

**주문 요청 테스트 (Windows - Command Prompt, Swagger 대신 선택):**

위 Linux/macOS 예시에서 `-d` 뒤에 있는 JSON 객체만 복사해 주석 없이 `erp-mini/order.json`에 저장합니다.
`corp_id`와 `items`가 있는 JSON 객체 전체를 사용하며, 파일 이름이 `order.json.txt`가 아닌지
확인하세요. CMD에서 `erp-mini`로 이동한 뒤 아래 명령만 실행합니다.

```cmd
curl.exe -X POST http://127.0.0.1:8310/orders -H "Content-Type: application/json" -d @order.json
```

**주문 요청 테스트 (Windows - PowerShell, Swagger 대신 선택):**

아래 블록 전체를 복사해 실행합니다. `$body`에는 비밀값이 없는 실습용 주문 JSON만 담습니다.

```powershell
$body = @'
{
    "corp_id": "11111111-1111-1111-1111-111111111111",
    "items": [
      {
        "product_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "quantity": 2
      },
      {
        "product_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "quantity": 1
      }
    ]
}
'@
Invoke-RestMethod -Uri "http://127.0.0.1:8310/orders" -Method Post -ContentType "application/json; charset=utf-8" -Body $body
```

---

<a id="ch10-install-help"></a>

## 패키지 설치 확인과 오류

**Python 3.12를 찾을 수 없을 때**

이 장은 Python 3.12를 사용합니다. `py` 명령을 찾을 수 없거나 `py -3.12 --version`이 실패하면
[기초 실습 환경 준비](../README.md#return-to-book)의 Python Install Manager 준비 절차를 확인합니다.
Install Manager가 설치되어 있다면 `pymanager install 3.12`로 Python 3.12를 설치합니다.
새 PowerShell을 열어 `py -3.12 --version`에서 `Python 3.12.x`가 나오는지 확인한 뒤 본문 Step 2로 돌아갑니다.
PC의 기본 Python 버전을 바꾸거나 다른 프로젝트의 Python을 삭제할 필요는 없습니다.

**가상환경 파일을 찾을 수 없을 때**

`Activate.ps1`이나 `.venv\Scripts\python.exe` 파일을 찾을 수 없다는 오류는 실행 정책 오류와 다릅니다.
현재 위치가 이번 장의 `erp-mini`인지 확인하고 `Test-Path -LiteralPath .\.venv\Scripts\python.exe`를 실행합니다.
`False`이고 아직 가상환경을 만들지 않았다면 본문 Step 2의 `py -3.12 -m venv .venv`부터 진행합니다.
생성 명령이 실패했다면 먼저 그 오류를 해결합니다. 기존 가상환경 폴더를 임의로 삭제하지 않습니다.

**다른 Python 버전에서 패키지 빌드가 실패했을 때**

`Failed building wheel for pyyaml`과 `Microsoft Visual C++ 14.0 or greater is required`가 함께 나오면,
현재 환경에서 PyYAML을 소스로 컴파일하려다가 C++ 빌드 도구가 없어 실패한 것입니다.
`uvicorn[standard]`를 설치할 때 PyYAML도 함께 설치됩니다. 먼저 `python --version`으로 현재 가상환경의 버전을 확인합니다.
오류 로그에 `cp315`나 `cpython-315`가 보인다면 Python 3.15용 환경을 뜻합니다.

3.12가 아니라면 이 실습에서는 Python 3.12로 가상환경을 새로 준비합니다. 아래는 3.15 환경에서 실패한 경우의 예시입니다.
서버를 종료하고, 가상환경이 활성화된 `erp-mini` 터미널에서 한 줄씩 실행합니다.
첫 확인에서 `Python 3.12.x`가 나오지 않으면 위 설치 안내부터 따릅니다.

```powershell
py -3.12 --version
deactivate
Rename-Item -LiteralPath .\.venv -NewName .venv-py315-backup
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python --version
```

기존 `.venv`는 이름만 바꿔 보관하며, 코드·`.env`·DB는 변경하지 않습니다.
이미 `.venv-py315-backup`이 있다면 다른 보관 이름을 사용합니다. 이름 변경이 실패하면 다음 명령으로 넘어가지 않습니다.
가상환경을 새로 만들어도 패키지는 자동으로 옮겨지지 않습니다. 마지막 출력이 `Python 3.12.x`인지 확인한 뒤 본문 Step 2의 패키지 설치·점검부터 다시 실행합니다.
3.12에서도 같은 빌드 오류가 나면 오류 마지막 부분을 확인하고 원인을 조사합니다. Python 버전만으로 모든 설치 오류가 해결되는 것은 아닙니다.

설치가 성공하면 `Successfully installed ...`, 이미 설치돼 있으면 `Requirement already satisfied ...`가
나올 수 있습니다. 마지막 `pip check`의 기대 결과는 `No broken requirements found.`입니다.

명령은 한 줄씩 실행하고, `venv` 생성이나 `pip install`에서 오류가 나면 다음 명령으로
넘어가지 않습니다. 오류 원인을 해결한 뒤 실패한 명령부터 다시 실행하세요. `pip check`는
이미 설치된 패키지 사이의 의존성만 검사하므로, 필요한 패키지를 설치하지 못했어도
`No broken requirements found.`가 나올 수 있습니다. 설치 성공과 의존성 검사 통과를
모두 확인한 뒤 Step 2의 `/health`를 확인합니다. 이미 확인한 독자는 이 도움말의 재개 표에서 중단한 위치로 돌아갑니다.

설치 중 `ERROR: Could not install packages due to an OSError`가 나오면 오류 번호와
마지막 메시지를 확인하세요. 경로 길이뿐 아니라 쓰기 권한이나 디스크 공간 등도 원인이 될 수 있습니다.
경로가 너무 길다는 메시지나 안내가 있다면 ZIP을 `C:\erp-book`처럼 짧은 위치에 새로 풀고
Step 2를 처음부터 다시 실행합니다. 다른 오류라면 표시된 원인을 먼저 해결하세요.
설치가 실패한 상태에서는 `pip check`가 통과해도 뒤에서 `No module named 'pg8000'` 같은
오류가 나타날 수 있습니다.

---

<a id="ch10-connection-options"></a>

## 연결 방식과 비밀번호 인코딩

- **Supabase 클라우드 사용 시**: [공통 부록의 Session pooler 주소 확인](supabase_project_setup.md#supabase-connect)을 따릅니다.
  10장은 pg8000을 사용하므로 `postgresql://` 시작 부분을 그대로 유지하고 `erp-mini/.env`의 `DATABASE_URL`에 저장합니다.
  11장의 `+psycopg2` 표기를 복사하지 않습니다. 사용자명·호스트·포트는 자신의 Chapter 10 프로젝트에서 복사한 값을 사용합니다.

  ```env
  DATABASE_URL=postgresql://postgres.[PROJECT_REF]:[ENCODED_PASSWORD]@[POOLER_HOST]:5432/postgres
  ```

  위는 형식 예시입니다. 대괄호 부분을 그대로 넣지 않습니다. 실제 주소의 비밀번호 부분을 채우고,
  특수문자가 있다면 [공통 부록의 URL 인코딩 설명](supabase_project_setup.md#supabase-password-encoding)을 먼저 읽습니다.
- **Docker 로컬 PostgreSQL 사용 시**: 앞서 설정한 비밀번호와 포트에 맞춰 아래와 같이 지정합니다.
  ```env
  DATABASE_URL=postgresql://postgres:your_password@localhost:5432/postgres
  ```

<a id="ch10-password-encoding"></a>

**비밀번호의 URL 인코딩**

처리 원리와 주의점은 [공통 부록의 비밀번호 인코딩](supabase_project_setup.md#supabase-password-encoding)을 따릅니다.
예를 들어 가짜 비밀번호 `demo@pass:1`은 `demo%40pass%3A1`로 적습니다. 10장의 `db.py`는 이 값을 한 번 디코딩해 DB에 전달합니다.

---

<a id="ch10-db-helper"></a>

## 제공 연결 코드 읽기

**2) PostgreSQL 연결 관리 (db.py)**

DB 연결 문자열(URI)은 `postgresql://[사용자명]:[비밀번호]@[호스트]:[포트]/[데이터베이스명]` 형태입니다.
아래 코드는 `urlparse()`로 주소를 나누고 사용자명·비밀번호·호스트·포트를 `pg8000`에 전달합니다.

```python
# db.py
from pathlib import Path
from urllib.parse import unquote, urlparse

import pg8000.dbapi
from dotenv import dotenv_values


LOCAL_ENV = Path(__file__).with_name(".env")

def get_connection():
    database_url = str(dotenv_values(LOCAL_ENV).get("DATABASE_URL") or "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    url = urlparse(database_url)
    if not all((url.username, url.password, url.hostname, url.path.lstrip("/"))):
        raise RuntimeError("DATABASE_URL format is invalid")

    return pg8000.dbapi.connect(
        user=unquote(url.username),
        password=unquote(url.password),
        host=url.hostname,
        database=url.path.lstrip("/"),
        port=url.port or 5432,
    )
```

키트의 `db.py`에는 위 코드가 이미 들어 있습니다. 이 함수는 운영체제의 환경 변수 대신
`db.py`와 같은 `erp-mini` 폴더의 `.env`에서 연결 문자열을 읽습니다. 연결 문자열을
출력해서 확인하지 말고 누락되었을 때 나타나는 오류 메시지로 설정 여부를 확인합니다.

URI에서 `%40`처럼 인코딩된 사용자명·비밀번호는 `unquote()`로 한 번 디코딩해 원래 문자로
복원합니다. `urlparse()`는 주소를 나누지만 인코딩된 문자를 자동으로 복원하지는 않습니다.

---

<a id="ch10-runtime-help"></a>

## 연결·서버·요청 오류 해결

> **[트러블슈팅] 실습 중 막혔을 때 해결법**
>
> 1. **데이터베이스 연결 실패**
>    - **증상**: Step 3의 `DB connection OK`가 나오지 않거나 관찰 화면이 503을 반환합니다.
>    - **확인 순서**: 아래에서 오류 메시지와 맞는 행을 확인하고 Step 3의 연결 명령을 다시 실행합니다.
>
>      | 오류·상황 | 확인할 내용과 다음 행동 |
>      | :--- | :--- |
>      | `No module named ...` | `erp-mini` 터미널에서 Step 2의 `.venv` Python으로 패키지를 설치하고 실행했는지 확인합니다. `pip install`이 실패했다면 오류 번호와 마지막 메시지로 원인을 확인합니다. 경로 길이 오류라면 위 [설치 도움말](#ch10-install-help)의 짧은 경로 안내를 따릅니다. |
>      | `DATABASE_URL is not configured` | `db.py` 옆에 `.env`가 있고 `DATABASE_URL` 값이 저장되어 있는지 직접 확인합니다. |
>      | `DATABASE_URL format is invalid`, 잘못된 포트 등 주소 오류 | Step 3의 URI 형태와 대괄호 치환을 확인합니다. 비밀번호의 예약 문자를 인코딩했는지도 확인합니다. |
>      | 호스트를 찾을 수 없음·타임아웃·네트워크 연결 불가 | Supabase 프로젝트 상태와 Connect의 주소를 확인합니다. 직접 연결을 사용 중이면 Session pooler URI 전체로 바꿔 봅니다. 로컬은 컨테이너 실행 상태와 포트 매핑을 확인합니다. |
>      | `password authentication failed` 등 인증 오류 | 선택한 방식의 사용자명과 DB 비밀번호를 확인합니다. Session pooler의 사용자명에는 프로젝트 식별자가 붙습니다. |
>      | 연결은 되지만 `relation ... does not exist` | 연결한 DB의 Table Editor에서 업무 테이블 8개와 표식 테이블을 확인합니다. 다른 DB를 준비했다면 연결 대상부터 맞춥니다. 재개 중이라면 `schema.sql`을 다시 실행하지 말고 기존 DB와 중단한 준비 작업을 확인합니다. |
>      | 연결 확인은 성공했지만 화면에 503 | 연결 확인은 표식·테이블까지 검사하지 않습니다. Chapter 10 표식, 업무 테이블 8개와 기초 데이터가 같은 전용 DB에 있는지 확인합니다. 새 DB라면 Step 3의 남은 준비를 마치고, 재개한 DB라면 기존 기록을 지우지 않습니다. |
>
>    `.env`와 연결 문자열은 AI에게 보내지 않습니다. 도움을 요청할 때는 비밀값과 접속 주소를
>    제외하고 오류 종류·연결 방식·연결 확인 성공 여부만 전달합니다.
> 
> 2. **서버 실행 실패 (`Address already in use` 또는 `Port 8310 is occupied`)**
>    - **증상**: `uvicorn` 실행 시 포트가 이미 사용 중이라는 에러와 함께 기동되지 않습니다.
>    - **해결책**: 다른 프로그램이 8310 포트를 사용 중이면 서버 명령의 `--port 8310`을 `--port 8311`로 바꿉니다. `.venv`의 Python으로 실행하는 부분은 그대로 사용합니다.
>      확인용 주소는 `http://127.0.0.1:8311/health`, 실습 화면은 `http://127.0.0.1:8311`입니다. 이후 서버 명령과 요청 URL도 모두 같은 포트를 사용합니다.
>      Step 2에서는 `/health` 응답을 다시 확인한 뒤 서버를 Ctrl+C로 종료합니다. Step 5에서 화면을 열 때 선택 스크립트를 쓴다면 `-Port 8311`을 붙입니다.
> 
> 3. **Pydantic 데이터 검증 실패 (`422 Unprocessable Entity`)**
>    - **증상**: API 호출 시 422 상태 코드가 반환됩니다.
>    - **해결책**: 요청으로 보낸 JSON의 필드 이름이나 중괄호(`{}`), 대괄호(`[]`) 구성을 확인하세요. `corp_id` 키가 누락되었거나, `items` 내부의 `product_id` 스펠링이 올바른지 검사해 보아야 합니다.
>
> 4. **첫 주문에서 재고 부족 오류가 나는 경우**
>    - **증상**: 응답에 `재고 부족`이 표시됩니다. 현재 예제 코드는 이 예외를 400 응답으로 반환합니다.
>    - **해결책**: Step 3의 초기 입고 SQL을 빠뜨리지 않았는지 확인하고 재고 조회 SQL을 실행하세요.
>      초기 입고를 누락한 새 DB라면 해당 SQL을 실행합니다. 이미 주문해 재고를 소비했다면 [재개 안내](#ch10-resume)에서 기존 기록을 먼저 확인합니다.

---

<a id="ch10-reset"></a>

## 로컬 코드와 DB 초기화

실습 결과를 복습 자료로 남기려면 초기화하지 않아도 됩니다. 처음부터 다시 진행하려면 API
서버를 먼저 종료하고, 로컬 파일과 데이터베이스를 각각 초기화합니다. 두 작업은 자동으로
연결되지 않습니다.

먼저 PowerShell에서 `foundation-lab-kit` 루트로 이동해 로컬 복원 대상을 확인합니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\reset_practice_chapter.ps1 -Chapter ch10
```

미리 보기에는 `db.py`, `schema.sql`, `server.py`, `test_orders.py`가 `_starter`의 시작 상태로 복원될 경로가
표시됩니다. 모든 경로가 `practice-workspace/ch10` 안에 있는지 확인한 뒤 적용합니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\reset_practice_chapter.ps1 -Chapter ch10 -Apply
```

개인 연결 문자열을 담은 `.env`는 자동으로 삭제하지 않습니다. 다시 사용할 필요가 없다면
내용을 화면이나 로그에 출력하지 말고 안전하게 제거합니다.

DB 객체까지 지우려면 현재 접속한 프로젝트가 Chapter 10 전용이고 보존할 데이터가 없는지
다시 확인합니다. 그런 다음 `erp-mini/sql/99_reset_lab.sql`의 삭제 대상을 읽고 SQL Editor에서
직접 실행합니다. 이 SQL은 `00_initialize_lab.sql`의 Chapter 10 표식이 없으면 예외를 발생시키며,
SQL에 이름이 명시된 테이블만 삭제합니다. 이 목록에는 주문용 8개 테이블과 `test_orders`가
포함되지만, 선택 실습의 `temp_sandbox_` 체험 테이블은 포함되지 않습니다. 남아 있는 체험용 테이블은
[체험 중단 후 다시 시작하기](#ch10-sandbox-restart)의 안내에 따라 별도로 정리합니다.
도구가 DB에 자동 접속하거나 연결 문자열을 읽는 일은 없습니다.

초기화가 끝나면 다음 명령으로 로컬 시작 파일을 다시 확인합니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\verify_practice_chapter.ps1 -Chapter ch10
```
