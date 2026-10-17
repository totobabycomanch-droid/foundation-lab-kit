# 작은 발주 예제 작업 규칙

<!-- common-rules-version: chapter8-v6 -->

## 조사와 승인 (approval-required)

- 이 폴더의 README.md와 ../ai_build_rules.md, ../ai_review_rules.md, ../chapter8_order_spec.md를 읽는다.
- 현재 폴더의 절대 경로와 기존 파일을 확인하고 변경 범위를 짧게 보고한다.
- 승인된 동일 범위는 이어서 진행한다. 이미 완성된 예제는 재작성 없이 검증한다.

## 생성 위치와 범위 (secrets-protected)

- 이 폴더의 order_example.py와 test_order_example.py만 생성하거나 수정한다.
- chapter8_order_spec.md의 공개 규격을 따른다. validate_item과 calculate_amounts의 이름·인자·반환 필드·ValueError를 맞추고 내부 구현은 자유롭게 정한다.
- checks/는 업무 규칙의 고정 검사이며 읽되 수정하지 않는다. 기존 함수가 다른 이름이면 공개 규격에 맞추되 업무 규칙과 테스트 기대값은 유지한다.
- Python 표준 라이브러리만 사용한다. DB·API·서버·외부 패키지를 만들거나 설치하지 않는다.
- reference/는 답안으로 읽거나 복사하지 않는다. 다른 실습 폴더와 .env·비밀 값은 읽거나 변경하지 않는다.

## 완료 근거 (evidence-scoped)

- python order_example.py로 세 사례의 실제 결과를 보여 준다.
- python -m unittest -v test_order_example.py로 최신 테스트를 실행한다.
- ../../../tools/verify_ch08_core.ps1로 생성 테스트와 고정 검사를 실행한다. 직접 관찰·AI 실행·테스트 근거를 구분한다.
- ../ai_review_rules.md에 따라 Pass·Fail·Not Run·테스트 없음과 파일·테스트 이름을 보고한다.
- DB 조회·저장·롤백·HTTP가 검증됐다고 주장하지 않는다.

## Python 대화형 직접 호출

- 독자는 python을 실행한 뒤 >>>에서 검증·계산 함수를 직접 호출한다.
- 수량 -3·0의 ValueError, 정상값 수정과 요청 단가 100원·10원 제외를 예상·관찰하게 한다.
- input()·별도 실행 옵션·재입력 질문을 필수로 구현하지 않는다. 기본 실행과 import는 입력을 기다리지 않는다.
