# Chapter 10 작업 규칙

- `erp-mini/`는 Chapter 10 전용이며 Chapter 9의 동명 폴더와 다른 프로젝트다.
- SQL은 폐기 가능한 Chapter 10 전용 Supabase 프로젝트 또는 로컬 PostgreSQL에서만 실행한다.
- `.env`와 실제 DB URL을 읽거나 출력하지 않는다.
- `DROP`과 `DELETE` 전에 현재 DB와 대상 테이블을 보고하고 승인받는다.


- 화면 실습의 기본 변경 범위는 erp-mini/server.py와 erp-mini/test_orders.py다. 자세한 공개 규약은 README.md를 따른다.
- verify_core.py --allow-test-writes는 이번 실행에서 새로 만든 ch10_verify_<UUID> 스키마의 생성·제거만 허용하며 기존 public 업무 테이블은 변경하지 않는다.
