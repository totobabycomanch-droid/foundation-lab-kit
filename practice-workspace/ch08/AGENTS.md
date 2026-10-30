# Chapter 8 작업 규칙

<!-- common-rules-version: chapter8-v7 -->

## 조사와 승인 (approval-required)

- 이 파일과 README.md를 읽고 실제 작업 폴더의 절대 경로를 확인한다.
- 개편 실습의 구현 루트는 understanding/이다. 해당 폴더의 AGENTS.md와 README.md를 읽는다.
- 기존 파일·변경 범위·확인 명령을 짧게 보고하고 승인된 범위만 수정한다.
- 이미 승인한 동일 범위는 이어서 진행하며, 기존 구현이 조건을 충족하면 재작성 없이 검증한다.

## 작업 범위 (secrets-protected)

- chapter8_order_spec.md의 작은 실습만 수행한다. 실제 ERP의 DB·API에 연결하지 않는다. 제공 로컬 관찰 서버로 업무 함수를 실행한다.
- project/, reference/, legacy-api/는 이전 API 실습 자료이다. 새 구현을 위해 읽거나 복사·수정하지 않는다.
- .env와 비밀 값, 다른 Chapter 파일은 읽거나 출력·변경하지 않는다.
- understanding/reference/는 막혔을 때 독자가 볼 참고 자료이며 AI 생성 답안으로 사용하지 않는다.
- understanding/checks/는 읽기 전용 고정 검사이다. 공개 함수 규격은 chapter8_order_spec.md를 따르며 검사와 업무 규칙의 기대값을 변경하지 않는다.

## 근거 확인 (evidence-scoped)

- 정상 5500·조작 단가 제외·수량 0의 계산 전 거부를 실제 테스트로 확인한다.
- 공백 제거·수량 제한·VAT 구분·104/105/106원 경계값도 확인한다. tools/verify_ch08_core.ps1은 understanding/에서 ../../../tools/verify_ch08_core.ps1로 실행한다.
- Pass·Fail·Not Run·테스트 없음과 코드 검토·명령 실행을 구분한다.
- 근거에는 파일 경로와 검색할 테스트 이름을 함께 보고한다.
- 세부 보고 기준은 ai_review_rules.md를 따른다. 실제 ERP API·DB 저장·롤백을 검증했다고 보고하지 않는다.

이 장의 저장 부분은 마스터·상세·감사를 함께 저장하는 이유를 읽는 과정이다.
실제 DB의 단가 조회·계산·원자 저장 구현은 Day 16에서 이어간다.


## 제공 화면과 업무 코드의 경계

- 화면·HTTP 연결은 제공 기능이다. 로컬 관찰 서버 사용은 허용하며 서버·화면·checks/·verify_web.py·지침은 학습자가 수정하지 않는다.
- 학습자 구현은 order_example.py와 test_order_example.py 두 파일이다. 제공 서버는 검증·계산을 대신하지 않는다.
- 정상·요청 단가 조작·서버 기준값 변경·수량 거부와 복구·VAT 미적용·104/105/106원 경계값을 화면에서 비교한다.
- 기본 포트는 8308이며 start_lab.ps1 -Port로 변경한다. Python 3.12 이상과 표준 라이브러리만 사용한다.
- 현재 폴더에서 python을 사용한다. Chapter 7의 .venv를 가져오거나 기존 API 실습 requirements.txt를 설치하지 않는다.
- 검증 실패 시 계산은 미실행이어야 한다. 입력과 실제 반환값·예외를 표시하고 이전 계산 결과를 재사용하지 않는다.
- 서버 단가는 실습용 별도 기준값이며 DB에서 조회한 값이 아니다. 실제 ERP의 가격 보안 경계를 검증했다고 주장하지 않는다.
- 화면의 관찰 내역 복사로 실제 실행 결과를 AI 검토에 제공한다. AI 검사를 독자의 직접 관찰로 보고하지 않는다.
- 검증은 ../../../tools/verify_ch08_core.ps1로 실행한다. 생성 테스트·고정 업무 검사·제공 연결 검사를 구분한다.
- 실제 ERP API·DB 조회·저장·롤백·동시 요청은 실습 대상이 아니다. 로컬 HTTP 연결 확인과 구분한다.
- import 시 예제나 입력 대기를 실행하지 않는다. Python 직접 호출은 선택이며 기본 화면 실습의 추가 완료 조건이 아니다.
- _starter/는 미구현 배포 시작본이다. 기존 학습자 파일을 시작본이나 reference/로 덮어쓰지 않는다.
