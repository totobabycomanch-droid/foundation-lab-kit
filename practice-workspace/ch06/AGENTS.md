# Chapter 6 작업 규칙

- 이 장에서는 도구와 실행 환경을 조사하며 업무 기능을 구현하지 않는다.
- 실제 `.env` 값은 읽거나 출력하지 않는다.
- Python, Node.js, npm과 Docker의 설치 여부를 각각 판정한다.
- 설치하지 않은 도구 때문에 실행할 수 없는 개별 검증은 `Not Run`으로 보고한다.
- `Not Run`은 개별 검증 결과에만 사용한다. 최종 `environment_report.md`에서는 필수 환경의 검증이
  하나라도 `Not Run`이면 `Needs Fix`로 판정하고, 아직 준비하지 않은 Supabase만 본문의 규칙에
  따라 `Deferred`로 판정한다.
