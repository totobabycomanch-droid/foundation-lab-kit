# Chapter 8 project 규칙

- 비즈니스 판단은 `services/`, 저장 기술은 `repositories/`, HTTP 연결은 `routers/`에 둔다.
- 라우터나 저장소에 재고·예치금 판단 규칙을 중복 작성하지 않는다.
- `.env`를 읽거나 출력하지 않으며 `.env.example`의 변수 이름만 참고한다.
- 변경 뒤 순수 로직 테스트와 Persistence dry-run을 각각 판정한다.

