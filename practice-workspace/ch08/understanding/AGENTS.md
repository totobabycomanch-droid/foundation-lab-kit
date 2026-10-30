# 작은 발주 예제 작업 규칙

<!-- common-rules-version: chapter8-v7 -->

## 조사와 승인 (approval-required)

- 이 폴더의 README.md와 ../ai_build_rules.md, ../ai_review_rules.md, ../chapter8_order_spec.md를 읽는다.
- 현재 폴더의 절대 경로와 기존 파일을 확인하고 변경 범위를 짧게 보고한다.
- ../ai_build_rules.md의 변경 전후 비교 절차에 따라 기존 변경과 비교 기준을 확인한다. 합의된 범위를 벗어날 때만 추가 확인을 받는다.
- 승인된 동일 범위는 이어서 진행한다. 이미 완성된 예제는 재작성 없이 검증한다.

## 생성 위치와 범위 (secrets-protected)

- 이 폴더의 order_example.py와 test_order_example.py만 생성하거나 수정한다.
- chapter8_order_spec.md의 공개 규격을 따른다. validate_item과 calculate_amounts의 이름·인자·반환 필드·ValueError를 맞추고 내부 구현은 자유롭게 정한다.
- checks/는 업무 규칙의 고정 검사이며 읽되 수정하지 않는다. 기존 함수가 다른 이름이면 공개 규격에 맞추되 업무 규칙과 테스트 기대값은 유지한다.
- Python 표준 라이브러리만 사용한다. 실제 DB·ERP API·외부 패키지를 추가하지 않는다. 제공 로컬 관찰 서버는 사용한다.
- reference/는 답안으로 읽거나 복사하지 않는다. 다른 실습 폴더와 .env·비밀 값은 읽거나 변경하지 않는다.

## 완료 근거 (evidence-scoped)

- python order_example.py로 세 사례의 실제 결과를 보여 준다.
- ../../../tools/verify_ch08_core.ps1로 생성 테스트와 고정 검사를 실행한다. 직접 관찰·AI 실행·테스트 근거를 구분한다.
- python -m unittest -v test_order_example.py는 생성 테스트 실패를 별도로 조사할 때 사용한다.
- ../ai_review_rules.md에 따라 Pass·Fail·Not Run·테스트 없음과 파일·테스트 이름을 보고한다.
- 기존 변경·이번 변경을 구분하고, 비교 기준이 없으면 변경 범위를 확인하지 못했다고 보고한다. 독자에게 Git 준비나 별도 관찰 기록을 요구하지 않는다.
- 실제 ERP API·DB 조회·저장·롤백이 검증됐다고 주장하지 않는다.


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
