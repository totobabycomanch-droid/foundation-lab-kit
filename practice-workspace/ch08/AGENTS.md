# Chapter 8 작업 규칙

<!-- common-rules-version: chapter8-v6 -->

## 조사와 승인 (approval-required)

- 이 파일과 README.md를 읽고 실제 작업 폴더의 절대 경로를 확인한다.
- 개편 실습의 구현 루트는 understanding/이다. 해당 폴더의 AGENTS.md와 README.md를 읽는다.
- 기존 파일·변경 범위·확인 명령을 짧게 보고하고 승인된 범위만 수정한다.
- 이미 승인한 동일 범위는 이어서 진행하며, 기존 구현이 조건을 충족하면 재작성 없이 검증한다.

## 작업 범위 (secrets-protected)

- chapter8_order_spec.md의 작은 실습만 수행한다. DB·API·서버를 만들거나 연결하지 않는다.
- project/, reference/, legacy-api/는 이전 API 실습 자료이다. 새 구현을 위해 읽거나 복사·수정하지 않는다.
- .env와 비밀 값, 다른 Chapter 파일은 읽거나 출력·변경하지 않는다.
- understanding/reference/는 막혔을 때 독자가 볼 참고 자료이며 AI 생성 답안으로 사용하지 않는다.

## 근거 확인 (evidence-scoped)

- 정상 5500·조작 단가 제외·수량 0의 계산 전 거부를 실제 테스트로 확인한다.
- Pass·Fail·Not Run·테스트 없음과 코드 검토·명령 실행을 구분한다.
- 근거에는 파일 경로와 검색할 테스트 이름을 함께 보고한다.
- 세부 보고 기준은 ai_review_rules.md를 따른다. DB 저장·롤백·HTTP를 검증했다고 보고하지 않는다.

이 장의 저장 부분은 마스터·상세·감사를 함께 저장하는 이유를 읽는 과정이다.
실제 DB의 단가 조회·계산·원자 저장 구현은 Day 16에서 이어간다.
