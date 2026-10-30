# Chapter 9 — 화면에서 주문 상태 규칙 확인하기

Python 3.12 이상과 브라우저를 사용합니다. 외부 패키지를 설치하지 않습니다.
VS Code와 PowerShell 위치는 practice-workspace/ch09/로 유지합니다.
화면·관찰 서버는 제공하고 주문 규칙·실행 예제·테스트 세 파일은 AI와 완성합니다.
상위 AGENTS.md, 이 폴더의 AGENTS.md와 erp-mini/AGENTS.md를 먼저 읽습니다.

## 실행

| 명령 | 용도 |
|---|---|
| ./run.ps1 check | 제공 파일과 시작 구조 확인 |
| ./run.ps1 web | http://127.0.0.1:8309 관찰 서버 실행 |
| ./run.ps1 demo | 실제 행동을 호출하는 예제 |
| ./run.ps1 test | AI 생성 테스트 |
| ./run.ps1 verify | 주문 규칙 고정 검사 35개 |
| ./run.ps1 verify-web | 제공 도구 무결성과 별도 서버 HTTP 연결 검사 |
| ./run.ps1 shell | 선택: Python 대화형 입력, exit()로 종료 |

주문 규칙은 erp-mini/domain/order.py, 실행 예제는 erp-mini/main.py,
생성 테스트는 erp-mini/tests/test_erp_flow.py에 둡니다.
관찰 서버는 같은 Order 객체의 공개 행동을 호출하며 실패 후에도 실제 상태를 다시 읽습니다.
새 주문은 별개 객체이며 기존 관찰 내역을 지우지 않습니다.
화면 새로고침은 주문을 유지하지만 복사할 관찰 내역은 다시 시작합니다.
서버 재시작 시 주문은 사라집니다. 코드 수정 뒤 Ctrl+C로 서버를 종료하고 재시작하세요.
서버는 로컬 메모리만 사용합니다. DB·실제 ERP API·동시 요청·멱등성 검증으로 표현하지 않습니다.

## 검사와 복구

고정 검사는 생성 구현의 전이 표에서 기대값을 가져오지 않습니다.
화면 연결 검사는 임시 서버를 사용하고 현재 실습 서버의 주문을 바꾸지 않습니다.
verify_observation.py와 observation-baseline.json은 제공 도구 변조를 확인합니다.
업무 구현·생성 테스트는 무결성 검사 대상이 아니므로 AI와 수정할 수 있습니다.
화면·서버·고정 검사·기반 파일은 독자의 생성 요청에서 수정하지 않습니다.
기반 검사 실패 시 파일·실행 결과를 보관하고 같은 배포본의 제공 파일을 복구합니다.

초기화는 ./run.ps1 reset으로 대상 경로를 미리 확인하고 보관 후 -Apply로 적용합니다.
관찰 서버를 먼저 종료하세요. 초기화는 생성 업무 파일을 삭제하며 제공 화면과 고정 검사를 보존합니다.
정상 생성·검증 중 reference/를 답안으로 읽거나 복사하지 않습니다.
막혔을 때만 reference/README.md를 따라 비교합니다.
선택 결함 실습은 fault-lab/order.py에서만 진행하며 ./run.ps1 fault로 확인합니다.
