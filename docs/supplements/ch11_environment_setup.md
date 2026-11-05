# Chapter 11 환경 준비와 실행 도움말

처음 시작한다면 [본문의 환경 준비](../11_chapter11.md#ch11-environment)를 마치고
[11.2의 구현 요청](../11_chapter11.md#ch11-api-prepare)을 실행합니다.
이 문서는 설치·연결 문제, 중단 후 재개, 새 키트에서 기존 DB를 재사용하거나 처음부터 재실습할 때 필요한 항목만 찾아보는 도움말입니다.

| 다시 시작하는 목적 | 사용할 절차 |
|---|---|
| 현재 결과를 보존하고 이어가기 | [중단 후 재개](#ch11-resume) |
| 기능 구현은 유지하고 A·B만 다시 확인하기 | [사례 재준비](#ch11-prepare-case) |
| DB 구조와 함수도 비우고 구현부터 다시 하기 | [완전 초기화](#ch11-clear-database) |

## 누가 무엇을 준비하나요?

| 독자 | AI |
|---|---|
| VS Code에서 키트의 `practice-workspace/ch11/` 열기 | 규칙과 연결 명세·현재 파일 조사 |
| Python 3.12·Node.js 실행 기반 준비 | 프로젝트 가상환경·기존 의존성 설치 확인 |
| 새 전용 Supabase 프로젝트 생성·로컬 `.env` 설정 | 대상 대조·접속 확인·SQL 작성과 적용 |
| 업무 조건 결정·서버 실행·종료·화면과 저장 결과 판단 | 별도 테스트 데이터로 자동 검사 |

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
이 장의 가상환경은 `workspace/erp-project/venv/`에 준비하며, `venv/Scripts/python.exe`를 직접 지정해 실행할 수 있습니다.
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

<a id="ch11-reuse-database"></a>

## 새 키트에서 기존 DB 재사용하기

처음 실습할 때는 새 전용 DB를 준비합니다. 이미 Chapter 11을 실습했고 같은 전용 DB로 복습하려면,
테이블을 삭제하는 대신 현재 구조와 새 키트의 명세를 대조합니다. **데이터 초기화와 새 기능 추가는 서로 다른 작업입니다.**

1. 새 키트를 별도 폴더에 풀고 VS Code에서 새 `ch11/`을 엽니다. 기존 개인 코드는 덮어쓰지 않습니다.
2. 새 폴더의 백엔드 로컬 `.env`에 재사용할 전용 프로젝트의 연결값과 참조 ID를 설정합니다. 대화에 값을 붙여 넣지 않습니다.
3. 아래 요청으로 기존 DB와 새 명세의 차이를 확인하고, 필요한 변경과 A·B 재준비를 진행합니다.

```text
새 키트에서 기존 Chapter 11 전용 DB를 재사용해 처음부터 다시 실습하겠습니다.
프로젝트 규칙과 연결 명세를 읽고 연결 대상·표식·SQL 적용 이력·기존 테이블과 함수를 조사해 주세요.
수량 입력·별도 저장·승인 기능이 현재 명세와 다른 부분을 확인해 주세요.
필요한 변경은 기존 테이블을 삭제하지 않는 별도 SQL 파일로 작성·적용하고, 새 작업 폴더의 API와 화면도 구현해 주세요.
이미 적용된 SQL 파일과 기존 개인 작업 폴더는 수정하지 마세요.
적용 이력을 확인할 수 없거나 명세와 다른 객체가 있으면 자동으로 채택·삭제하지 말고 차이와 필요한 조치를 알려 주세요.

준비가 끝나면 A·B의 기존 결과를 지우고 두 주문을 수량 1·승인 대기·원장 0건으로 재준비해 주세요.
각 상품의 재고는 A가 10, B가 2로 복원하고 다른 데이터는 보존해 주세요.
관련 검사는 별도 데이터로 실행하고 A·B는 시작 상태로 남겨 주세요.
실제 DB의 재준비 결과·검사 결과·화면 주소·남은 문제를 알려 주세요. 연결값이나 비밀번호는 출력하지 마세요.
```

이전 버전 DB에는 수량 저장 함수가 없을 수 있습니다. 초기화 SQL이나 `prepare --reset`만 실행해도
새 함수가 생기는 것은 아닙니다. 기존 DB에서 `lab.py init`을 다시 실행하거나 전체 스키마를 중복 적용하지 않습니다.
구조를 맞춘 뒤에는 [두 사례의 재준비 결과](../11_chapter11.md#ch11-check-retry)를 확인하고 A부터 시작합니다.

## 중단 후 다시 시작하기

<a id="ch11-resume"></a>

같은 `ch11/` 폴더를 열고 다음처럼 요청합니다.

```text
프로젝트 규칙을 읽고 현재 SQL 적용 이력·DB의 두 주문·서버 상태를 조사해 중단한 실습을 이어서 진행해 주세요.
기존 코드와 관찰 결과를 보존하고 필요한 설치·적용·자동 검사만 수행해 주세요.
화면 테스트용 서버 실행·종료는 제가 직접 하겠습니다. 검사에 필요한 임시 서버는 검사 후 종료해 주세요.
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

서버 실행·종료는 독자가 직접 합니다. 도구가 관리하는 두 서버를 종료하려면 다음을 실행합니다.

```powershell
& .\venv\Scripts\python.exe lab.py servers stop
```

API·웹을 구분해야 할 때는 `--service api` 또는 `--service web`을 붙입니다.
전체 명령 설명은 키트의 `practice-workspace/ch11/README.md`에 있습니다.

<a id="ch11-prepare-case"></a>

## 같은 사례를 다시 확인하고 싶을 때

Core에서는 A와 B 사이에 재준비가 필요하지 않습니다.
현재 결과를 보존해 이어갈 때는 [중단 후 재개](#ch11-resume)를 사용하고, 결과를 지우고 반복할 때만 재준비합니다.
복습을 위해서만 “A만 시작 상태로 재준비해 주세요”처럼 대상을 지정합니다.
AI는 현재 결과를 먼저 확인하고 해당 주문·상품·원장만 복원합니다.

두 사례를 모두 지우고 다시 시작하려면 [본문의 A·B 재준비 요청](../11_chapter11.md#ch11-check-retry)을 사용합니다.

<a id="ch11-manual-reset"></a>

### AI 없이 도구를 직접 실행하기

수동 실행이 꼭 필요하다면 기존 결과를 보존한 뒤, 전용 DB 대상과 A를 되돌릴 의도를 확인하고 다음 명령을 사용합니다.

```powershell
& .\venv\Scripts\python.exe lab.py prepare --case A --reset
& .\venv\Scripts\python.exe lab.py state
```

A는 수량 1·`CREATED`·재고 10·원장 0건으로 돌아갑니다. B만 복습하려면 `--case B`를 지정하며 수량 1·시작 재고 2로 돌아갑니다.
각 사례를 다시 확인할 때는 수량을 3으로 입력·저장한 뒤 승인합니다.
원장 증감량은 행이 없으므로 `NULL`입니다. 화면도 다시 조회해 저장 상태와 맞춥니다.

두 사례를 함께 재준비하려면 첫 명령을 다음과 같이 바꿉니다.

```powershell
& .\venv\Scripts\python.exe lab.py prepare --case all --reset
& .\venv\Scripts\python.exe lab.py state
```

### SQL Editor에서 직접 초기화하기

터미널 도구 대신 Supabase에서 직접 실행할 수도 있습니다. 아래 SQL은 **A·B의 원장을 삭제하고 주문 수량·승인 상태·재고를 복원**합니다.
테이블·함수·SQL 적용 이력은 유지하며, 새 수량 저장 기능을 추가하지 않습니다.

1. 실습 서버를 종료하고 기존 Chapter 11 전용 Supabase 프로젝트인지 확인합니다.
2. `workspace/erp-project/sql/view_orders.sql`을 SQL Editor에서 실행해 A·B의 주문명·상품·현재 결과를 확인합니다.
   두 주문이나 상품이 다르거나 같은 상품을 다른 주문에서도 사용한다면 실행하지 말고 AI에게 조사를 요청합니다.
3. A·B 결과를 지울 의도가 맞다면 **SQL Editor → 새 쿼리**에서 아래 SQL 전체를 실행합니다.

```sql
BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM public.foundation_lab_marker WHERE lab_id = 'chapter11'
    ) THEN
        RAISE EXCEPTION 'Chapter 11 전용 실습 DB 표식이 없습니다.';
    END IF;
    IF EXISTS (
        SELECT 1 FROM public.orders
        WHERE product_id IN ('PROD-100', 'PROD-200')
          AND order_id NOT IN (
              '00000000-0000-0000-0000-000000000001'::uuid,
              '00000000-0000-0000-0000-000000000002'::uuid
          )
    ) THEN
        RAISE EXCEPTION '다른 주문이 실습 상품을 함께 사용하고 있습니다.';
    END IF;
END;
$$;

DELETE FROM public.stock_ledger
WHERE order_id IN (
    '00000000-0000-0000-0000-000000000001'::uuid,
    '00000000-0000-0000-0000-000000000002'::uuid
);

UPDATE public.orders SET quantity = 1, status = 'CREATED'
WHERE order_id IN (
    '00000000-0000-0000-0000-000000000001'::uuid,
    '00000000-0000-0000-0000-000000000002'::uuid
);

UPDATE public.stock
SET quantity = CASE product_id
    WHEN 'PROD-100' THEN 10
    WHEN 'PROD-200' THEN 2
END
WHERE product_id IN ('PROD-100', 'PROD-200');

COMMIT;
```

4. 같은 조회 SQL을 다시 실행합니다. A는 수량 1·`CREATED`·재고 10·원장 0건·증감량 `NULL`,
   B는 수량 1·`CREATED`·재고 2·원장 0건·증감량 `NULL`이어야 합니다.
5. 화면을 열거나 새로고침하고 각 주문의 수량을 3으로 입력·저장하는 실습을 시작합니다.

실행 중 오류가 발생하면 같은 쿼리 창에서 `ROLLBACK;`을 실행하고 원인을 확인합니다.
전용 표식이나 필요한 테이블이 없다는 오류를 우회하려고 조건을 지우지 말고, [기존 DB 재사용 안내](#ch11-reuse-database)로 돌아갑니다.

이 작업은 코드 초기화와 다릅니다. 키트의 `reset_practice_chapter.ps1`은 코드 복원 도구이며 DB 결과를 되돌리지 않습니다.
`workspace/sql/99_reset_lab.sql`은 테이블·함수·실습 표식·SQL 적용 이력을 제거하는 완전 초기화용입니다.
A·B 재준비에는 사용하지 않으며, DB를 비우려면 아래 완전 초기화 절차를 따릅니다.

<a id="ch11-clear-database"></a>

## DB를 비우고 구현부터 다시 시작하기

여기서 **빈 DB**란 Chapter 11에서 만든 실습 테이블·함수·표식·SQL 적용 이력이 없는 상태입니다.
Supabase 프로젝트와 관리 스키마·확장 객체, 로컬 코드와 `.env`는 유지합니다.
다음 대상의 데이터는 모두 사라지므로, 기존 결과를 남길 필요가 없는 전용 실습 DB에서만 진행하세요.

| 삭제 대상 | 범위 |
|---|---|
| 업무 테이블 | `public.stock_ledger`, `public.orders`, `public.stock`과 그 안의 모든 행 |
| 업무 함수 | `public.approve_order(UUID, VARCHAR, INTEGER)`, `public.change_order_quantity(UUID, INTEGER)` |
| 준비 기록 | `public.foundation_lab_marker`, `public.ch11_sql_history` |
| 소유 시퀀스 | 삭제하는 테이블의 자동 번호 시퀀스 |

실습 표식만 남으면 최초 준비 판단이 꼬일 수 있고, SQL 이력만 남으면 삭제한 스키마를 이미 적용했다고 판단할 수 있습니다.
완전 초기화에서는 이 둘도 함께 제거합니다.

### AI에게 완전 초기화 요청하기

1. 기존 실습을 실행하던 폴더에서 관리 서버를 종료합니다. 다른 프로그램의 서버를 임의 종료하지 않습니다.
2. 완전 초기화 명령이 포함된 키트를 별도 폴더에 준비하고, 로컬 `.env`에 같은 Chapter 11 전용 프로젝트의 연결값을 설정합니다.
3. 아래 프롬프트로 삭제할 의도와 범위를 명시합니다. 단순히 “초기화해 줘”라고만 하면 A·B 재준비와 구분하기 어렵습니다.

```text
이 프로젝트는 제가 Chapter 11 실습에만 사용하는 전용 DB에 연결돼 있습니다.
기존 실습 결과를 모두 버리고 빈 실습 DB에서 구현부터 다시 시작하겠습니다.
이번 요청은 A·B 데이터 재준비가 아니라 DB 완전 초기화이며, 지정 실습 객체와 모든 실습 결과의 삭제를 승인합니다.

프로젝트 규칙과 연결 명세를 읽고 전용 연결 대상·실습 표식·현재 객체를 확인해 주세요.
도구 실행에 필요한 환경이 없다면 기존 의존성 파일로 준비해 주세요.
관리 서버를 종료한 뒤 제공된 완전 초기화 명령으로 실습 테이블·두 업무 함수·표식·SQL 적용 이력을 함께 제거해 주세요.
Supabase 관리 스키마·확장 객체·로컬 코드·.env는 보존해 주세요.
다른 용도의 객체·함수나 외부 의존성이 있으면 삭제 범위를 넓히지 말고 중단해 차이를 알려 주세요.
지정 대상과 범위가 맞으면 위 삭제 승인을 적용해 진행해 주세요.
완료 후 실제로 실습 객체가 없어졌는지 확인해 주세요. 아직 표식·테이블·데이터를 다시 만들거나 서버를 시작하지 마세요.
연결값이나 비밀번호는 출력하지 마세요.
```

키트 지침은 이 명시적인 요청에 한해 지정 객체 삭제를 허용합니다. 보존 규칙을 이유로 일괄 거절하는 대신,
대상 불일치나 예상 밖 객체처럼 실행을 막는 실제 조건을 보고하게 합니다.

### 도구 또는 SQL Editor에서 직접 실행하기

Python 가상환경과 의존성이 준비돼 있다면, 서버를 종료한 뒤 **백엔드 `workspace/erp-project/`**에서 실행합니다.
`--confirm CHAPTER11`은 전체 실습 결과를 지우겠다는 명시적 확인값입니다.

```powershell
& .\venv\Scripts\python.exe lab.py clear-database --confirm CHAPTER11
```

`database: cleared` 결과는 삭제와 결과 확인 뒤 트랜잭션이 확정됐다는 뜻입니다.
이 명령은 로컬 연결 대상과 표식을 확인하며, 예상 밖 객체·함수나 의존성이 있으면 삭제를 취소합니다.
일반 SQL 적용 명령인 `lab.py apply`로 초기화 SQL을 실행하지 않습니다.

SQL Editor를 사용하려면 프로젝트 이름과 전용 용도를 직접 확인하고, 관리 서버를 종료한 뒤
[완전 초기화 SQL](../../practice-workspace/ch11/workspace/sql/99_reset_lab.sql) 파일 전체를 새 쿼리에 붙여 넣어 한 번 실행합니다.
키트에서는 `workspace/sql/99_reset_lab.sql`입니다. 전용 명령도 이 파일을 사용합니다.
파일의 단일 `DO` 블록은 삭제 전체가 성공하거나 함께 취소되도록 구성돼 있습니다.
오류가 나면 조건을 지우거나 `CASCADE`를 추가하지 말고 원인을 확인합니다.

### 빈 실습 DB 확인과 다음 실습

SQL Editor에서는 다음 조회로 확인할 수 있습니다. 두 조회의 모든 칸이 `NULL`이어야 합니다.

```sql
SELECT to_regclass('public.stock_ledger') AS stock_ledger,
       to_regclass('public.orders') AS orders,
       to_regclass('public.stock') AS stock,
       to_regclass('public.foundation_lab_marker') AS marker,
       to_regclass('public.ch11_sql_history') AS sql_history;

SELECT to_regprocedure('public.approve_order(uuid,character varying,integer)') AS approve_order,
       to_regprocedure('public.change_order_quantity(uuid,integer)') AS change_order_quantity;
```

표식이 없어졌으므로 이 시점의 `lab.py inspect`나 `state`, `view_orders.sql`로는 기존 실습 결과를 조회할 수 없습니다.
기존 개인 코드 폴더를 보존하고 새 키트의 미구현 시작 폴더에서 [환경 준비](../11_chapter11.md#ch11-environment)를 확인한 뒤
[11.2의 생성 프롬프트](../11_chapter11.md#ch11-api-prepare)를 실행합니다.
AI가 빈 실습 DB 조건을 확인해 최초 표식과 적용 이력을 준비하고, 새로 생성한 SQL·API·화면을 연결합니다.

[본문으로 돌아가기](../11_chapter11.md#ch11-after-environment)
