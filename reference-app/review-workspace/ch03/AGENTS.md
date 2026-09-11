# Chapter 3 AI 답변 교차 검증 규칙

- `backend/`, `frontend/`, `database/`, `checkpoints/`는 읽기와 테스트 실행만 허용한다.
- 이 폴더에서는 `ai-a-verdict.md`, `ai-b-verdict.md`, `comparison.md`만 생성하거나 갱신한다.
- `expected-verdict.md`와 `*-template.md`는 읽기 전용이다.
- 독립 판정 단계에서는 다른 AI의 결과와 `expected-verdict.md`를 읽지 않는다.
- 비교 단계에서만 두 판정과 `expected-verdict.md`를 함께 읽고 실제 소스를 다시 확인한다.
- 토큰, `.env` 값, 실제 연결 문자열과 개인정보를 결과 파일에 기록하지 않는다.
- 실행하지 않은 테스트는 `Not Run`, 존재하지 않는 테스트는 `테스트 없음`으로 구분한다.
- AI 간 다수결로 결론을 정하지 않고 실제 코드, DDL과 테스트 근거를 우선한다.
