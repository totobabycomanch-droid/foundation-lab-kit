# Chapter 11 workspace 규칙

- backend는 `erp-project/`, frontend는 `frontend-project/`에 둔다.
- 실제 `.env` 값을 읽거나 출력하지 않는다.
- DB 함수의 원자성, API 오류 변환, 화면 중복 클릭 방지를 각각 검증한다.
- 실행하지 않은 Supabase·브라우저 검증은 `Not Run`으로 보고한다.

