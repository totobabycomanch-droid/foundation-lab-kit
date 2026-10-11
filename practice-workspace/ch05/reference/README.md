# Chapter 5 참고 SQL

먼저 AI가 만든 sql/ 파일을 실행하고 조회 결과를 확인합니다. 막힌 부분을 비교할 때만 이 폴더의
같은 이름의 파일을 엽니다. 참고 파일의 결과를 자신이 생성한 파일의 실행 결과로 보고하지 않습니다.

- 01_current_and_history.sql: 현재값 7과 입고 10·출고 -3의 이력 비교
- 02_relationship_and_delete.sql: 외래 키 삭제 차단과 목록 제외 후 거래 보존

각 파일 전체를 기초 실습 전용 PostgreSQL SQL Editor에서 실행합니다.
임시 테이블은 COMMIT에서 정리되며 영구 업무 테이블은 변경하지 않습니다.
