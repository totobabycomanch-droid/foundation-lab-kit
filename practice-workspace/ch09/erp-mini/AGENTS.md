# Chapter 9 erp-mini 규칙

- 상태와 전이 규칙은 `domain/`, 흐름 조율은 `services/`, HTTP 변환은 `routers/`에 둔다.
- 9.4 테스트가 통과하기 전에 9.5 확장을 적용하지 않는다.
- 현재 상태와 요청 전이를 함께 확인하며 실패를 HTTP 성공으로 숨기지 않는다.

