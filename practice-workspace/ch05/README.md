# Chapter 5 — 현재값·이력과 데이터 관계

두 SQL 예제로 현재 수량과 그 값이 된 이유를 구분하고, 거래가 참조하는 상품을 지우는 것과
목록에서 제외하는 것을 비교합니다. API나 승인 함수를 만들지 않습니다.

## 시작과 실행

1. VS Code에서 이 ch05/ 폴더를 엽니다.
2. 저장소 접근형 AI에게 AGENTS.md와 README.md를 읽고 두 예제를 만들도록 요청합니다.
3. 생성된 각 SQL 파일 전체를 기초 실습 전용 Supabase SQL Editor에서 실행합니다.
4. 실제 조회 결과를 AI에게 전달하고 검증 근거를 확인합니다.

| 생성 파일 | 확인할 결과 |
|---|---|
| sql/01_current_and_history.sql | 현재값 7, 입고 10·출고 -3 두 행, 이력 합계 7 |
| sql/02_relationship_and_delete.sql | 상품 삭제 차단, 목록 0건, 상품·거래 각 1건과 연결 보존 |

각 파일은 독립적인 임시 테이블을 사용합니다. 전체 실행이 끝나면 정리되므로 반복 실행을 위해
초기화 파일을 실행할 필요가 없습니다. 기존 실습 결과를 보존하는 방식의 예제는 아닙니다.

- 상세 실행 단위와 필수 검사: [sql/README.md](sql/README.md)
- 막힌 뒤 비교할 참고 SQL: [reference/README.md](reference/README.md)

참고 파일은 reference/ 안에 있고 생성 파일은 sql/ 바로 아래에 있습니다. 같은 파일명이어도
경로가 다릅니다. 생성·검증은 독자가 만든 sql/ 파일을 대상으로 합니다.

기존 sql/00_initialize_lab.sql과 sql/99_reset_lab.sql은 이전 실습의 보관 파일입니다.
새 Core에는 사용하지 않습니다. 이전 DB를 정리하려는 경우에만 내용을 확인하세요.
