# Chapter 9 작업 규칙

- 생성·검증 전에 상위 `practice-workspace/AGENTS.md`의 공통 보고 규칙을 읽고 따른다.
  상위 지침을 읽는 것은 허용하며, 다른 Chapter의 파일은 읽거나 수정하지 않는다.
- `erp-mini/`는 Chapter 9 전용이며 Chapter 8 결과를 복사하지 않는다.
- 코드 생성·실행은 9.4의 단일 Order 예제와 테스트에서 마친다.
- 9.5는 책임 분리를 읽는 구간이며 Payment·Inventory나 서버 코드를 추가하지 않는다.
- 허용되지 않은 역전이와 상태 점프를 테스트로 먼저 표현한다.
- 상태 필드를 외부에서 직접 대입하는 우회 경로를 만들지 않는다.
- `checks/`와 `reference/`는 수정하지 않는다. 정상 생성·검증 중 `reference/`를 답안으로 읽거나 복사하지 않는다.
- 생성 테스트와 별도로 키트 루트의 `tools/verify_ch09_core.ps1`을 실행한다.
  고정 검사 통과를 main.py·생성 테스트의 내용 검토나 DB·HTTP 검증으로 확대하지 않는다.

