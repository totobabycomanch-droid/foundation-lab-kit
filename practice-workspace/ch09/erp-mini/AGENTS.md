# Chapter 9 erp-mini 규칙

- 상태와 전이 규칙은 `domain/order.py`, 직접 실행은 `main.py`, 자동 검사는 `tests/test_erp_flow.py`에 둔다.
- Python 표준 라이브러리만 사용하고 테스트는 `unittest`로 작성한다. DB와 HTTP는 연결하지 않는다.
- 허용되지 않은 행동은 거부하고 기존 상태를 유지한다. 공개 `status`에 직접 대입하는 우회 경로를 만들지 않는다.
- 9.5는 읽기 구간이다. Payment·Inventory·조율 서비스·라우터를 추가하지 않는다.

