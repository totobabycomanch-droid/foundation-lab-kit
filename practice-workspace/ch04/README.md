# Chapter 4 발주 승인 실습

업무 회의에서 역할·회사 규칙을 정하고, AI와 승인 규칙을 구현한다.
제공된 확인 화면으로 재승인 사건을 확인하고 상태 규칙을 보완한 뒤, 회사 경계 결함을 고친다.

## 실행과 확인 화면

Python 3.12 이상과 Node.js 22 이상을 준비하고 이 ch04 폴더를 VS Code에서 연다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_lab.ps1
```

기본 주소는 http://127.0.0.1:8304 이다. 종료는 실행 터미널의 Ctrl+C다.
포트가 사용 중이면 -Port 8305를 붙이고 브라우저도 같은 포트로 접속한다.
첫 실행에는 인터넷 연결이 필요하며 .venv와 node_modules를 준비한다.
화면에는 사용자 선택, 발주 목록·상세, 실제 서버 응답이 이미 준비되어 있다.
4.1의 회의를 읽고 4.2의 승인 권한 구현 프롬프트를 실행한 뒤 브라우저를 새로고침한다.

## 제공하는 기반과 AI가 구현할 기능

| 구분 | 제공 파일 | 독자 작업 |
|---|---|---|
| 서버·API | backend/app.py | 유지 |
| DB·초기화 | backend/store.py | 유지 |
| 사용자·세션 | backend/lab_auth.py | 유지 |
| HTTP 응답 전달 | frontend/transport.js | 유지 |
| HTML·공통 스타일 | frontend/index.html, frontend/style.css | 유지 |
| 승인 판단 | backend/approval_rules.py | 4.2 역할, 4.3 상태 구현 |
| 확인 화면 | frontend/app.js | 유지 |
| 승인 버튼 | frontend/approval-action.js | 4.2 조회 담당자 제한 구현 |
| 회사 조건 | backend/defect_scope.py | 4.4 조회 조건 수정 |
| 비교·복구 | _starter/의 세 작업 파일 | 읽기 전용 |

함수의 한글 docstring을 읽으면 입력값의 출처와 판단·저장 흐름을 확인할 수 있다.

## 실습 순서

원고 04_chapter4.md 또는 lessons/의 해당 실습을 기준으로 진행한다.
본문을 따라가는 독자는 lessons/를 따로 실행할 필요가 없다.

1. 실습 1: 첫 회의에서 역할과 회사 범위를 정한다.
2. 실습 2: 서버의 승인 권한과 조회 담당자의 승인 버튼 제한을 구현하고, 제공된 화면에서 확인한다.
3. 실습 3: 같은 발주에 두 번 요청해 사건을 확인하고 상태 검사를 추가한다.
4. 실습 4: 같은 화면의 회사 경계 결함 실습에서 결함을 관찰하고 원인을 읽은 뒤 서버의 회사 조회 조건만 고친다.

정상·거부 요청과 DB 값을 확인하는 것이 필수다. 관찰 기록·보고문·캡처 작성은 필수가 아니다.
원하는 독자는 제공된 화면으로 원고의 시연 대화를 따라 업무 규칙을 설명한다.

## 사용자·데이터·API

서버는 a_reader(A회사 READER), a_manager(A회사 MANAGER), b_manager(B회사 MANAGER)를 제공한다.
사용자 선택은 로컬 실습용이며 회사·역할은 서버가 정한다.
본 실습(main)과 회사 경계 결함 실습(defect)은 DB·세션·쿠키가 별개다.

| 발주 | 회사 | 시작 상태 | 승인 처리 횟수 |
|---|---|---|---:|
| 1001 | A | PENDING | 0 |
| 1002 | A | APPROVED | 1 |
| 2001 | B | PENDING | 0 |

다음 API 표는 제공된 화면이 사용하는 실제 계약이다.
독자가 파일 전문이나 API 표를 프롬프트에 복사할 필요는 없다.

| Method | /api/{space} 뒤 경로 | 입력·결과 |
|---|---|---|
| POST | /session | {"user_id":"a_reader"} 등. 서버 사용자 객체 반환, 세션 쿠키 설정 |
| GET | /me | 현재 user_id·corp_id·role·display_name, 미접속은 401 |
| GET | /orders | 자기 회사 발주 목록 |
| GET | /orders/{id} | 자기 회사 발주 상세, 타회사·없는 번호는 404 |
| POST | /orders/{id}/approve | 성공 시 갱신된 발주. 실제 거부 응답을 그대로 표시 |
| POST | /reset | 선택한 실습의 데이터·세션 초기화, 요청 중이면 409 |

발주에는 id·corp_id·item_name·quantity·status·approval_count가 있다.
send(space,path,method,data)는 {status,body}를 반환한다. 접속 쿠키는 자동 전달한다.
승인 후 /orders 또는 상세를 다시 조회하고, 승인 응답과 재조회한 상태·횟수를 함께 보여 준다.
사용자 전환 뒤에는 메뉴와 상세를 다시 연다. 초기화 후에는 사용자를 다시 선택한다.
서버 재시작은 DB를 보존하고 세션은 해제한다. 코드 변경은 초기화로 되돌아가지 않는다.

## 제공 파일 검사와 복구

```powershell
python verify_observation.py
```

이 검사는 제공 파일(frontend/app.js 포함)과 시작 기준본의 변경만 확인한다.
업무 동작은 브라우저와 API에서 별도로 확인한다. 검사 기준을 바꾸어 실패를 감추지 않는다.
복구 전에는 현재 Chapter 폴더를 보관하고, AI가 이번 변경 범위를 먼저 설명하게 한다.
화면이 바뀌었다면 같은 버전 키트의 frontend/app.js로 복원한다. 승인 버튼은 frontend/approval-action.js를
시작 기준본과 비교하고, 상태 규칙은 해당 단계의 승인 판단만 보완한다.
같은 버전 키트의 제공 파일을 복원할 때도 독자가 이미 만든 업무 코드는 보존한다.

## 실습 4 완료 후 선택 API 검증

```powershell
.\.venv\Scripts\python.exe .\verify_business_rules.py
```

두 실습의 정상·권한·상태·회사·미접속·없는 발주·회사 값 위조 등 24개 사례를 임시 사본에서 확인한다.
완성 사본의 기대 결과는 RESULT Pass=24 Fail=0 Not Run=0, 종료 코드 0이다.
시작본과 중간 단계는 아직 구현하지 않은 규칙 때문에 실패할 수 있다.
반환 코드 1은 기준 실패, 2는 환경·미실행 문제다. 실제 실패·미실행 이유를 확인한다.
기존 실습 DB와 실행 서버는 사용하지 않는다. 화면 버튼·동시 요청·저장 실패는 이 도구의 검사 범위 밖이다.
