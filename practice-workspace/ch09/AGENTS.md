# Chapter 9 작업 규칙

- 생성·검증 전에 상위 `practice-workspace/AGENTS.md`의 공통 보고 규칙을 읽고 따른다.
  상위 지침을 읽는 것은 허용하며, 다른 Chapter의 파일은 읽거나 수정하지 않는다.
- 생성·검증의 공개 사용 규약과 세부 기준은 `erp-mini/AGENTS.md`를 읽고 적용한다.
- `erp-mini/`는 Chapter 9 전용이며 Chapter 8 결과를 복사하지 않는다.
- 코드 생성은 9.4의 Order 예제와 테스트에서 마친다. 화면은 ./run.ps1 web으로 실행하며 실제 Order 객체의 공개 행동과 상태를 관찰한다.
- 9.5는 책임 분리를 읽는 구간이며 Payment·Inventory나 서버 코드를 추가하지 않는다.
- 허용되지 않은 역전이와 상태 점프를 테스트로 먼저 표현한다.
- 상태 필드를 외부에서 직접 대입하는 우회 경로를 만들지 않는다.
- `checks/`와 `reference/`는 수정하지 않는다. 정상 생성·검증 중 `reference/`를 답안으로 읽거나 복사하지 않는다.
- 독자의 PowerShell 위치는 `ch09/`로 유지한다. 예제·대화형 실행·생성 테스트·고정 검사는
  `./run.ps1 demo`, `./run.ps1 shell`, `./run.ps1 test`, `./run.ps1 verify`로 실행한다.
- 시작 구조 확인은 `./run.ps1 check`, 선택 결함 검사는 `./run.ps1 fault`를 사용한다.
- 초기화는 `./run.ps1 reset`으로 대상을 미리 확인한 뒤 `./run.ps1 reset -Apply`로 적용한다.
- `run.ps1`, web_server.py, frontend/, verify_observation.py, observation-baseline.json은 제공 관찰 도구이므로 독자의 코드 생성·수정 범위에 넣지 않는다.
- 화면의 실패 전후 상태를 관찰 도구가 복원하거나 예상값으로 대체하면 안 된다.
- ./run.ps1 verify-web은 제공 기반과 실제 HTTP 연결을 별도 임시 서버에서 검사한다. 현재 실행 서버의 주문을 변경하지 않는다.
- 코드를 수정하면 서버를 재시작하고 새 주문으로 다시 검증한다. 화면 새로고침은 코드 재적용이 아니다.
- 생성 테스트와 별도로 `./run.ps1 verify`를 실행한다.
  고정 검사 통과를 main.py·생성 테스트의 내용 검토나 DB·실제 ERP HTTP 검증으로 확대하지 않는다.

