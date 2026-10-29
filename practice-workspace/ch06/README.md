# Chapter 6 시작점

Chapter 7~11과 Day 00에서 사용할 모든 도구를 이 장에서 한 번에 준비하고 확인하는 공간입니다.
Python 3.12, Chapter 7 전용 가상환경, Node.js·npm, Docker·Compose와 Supabase 조회까지 포함합니다.
이 폴더에는 실제 비밀값을 만들지 않습니다. 공개 변수 이름은 `.env.tools.example`만 참고합니다.

- 도구 설치를 마치면 AI에게 환경을 직접 확인하고 environment_report.md를 작성해 달라고 요청합니다.
  버전·경로·날짜를 별도 양식에 정리해 넣지 않아도 됩니다.
- AI는 AGENTS.md가 허용한 조회와 Chapter 7 가상환경·메모리 SQLite 확인만 실행합니다.
  설치·다운로드·설정 변경은 하지 않으며 environment_report.md 외의 파일은 수정하지 않습니다.
- Supabase 등 직접 접근할 수 없는 항목만 AI가 하나씩 안내합니다. SQL Editor에서 확인했다면
  오늘 실행했는지와 connection_check가 1인지 답하면 됩니다. 비밀번호나 API 키는 전달하지 않습니다.
- AI가 다른 PC나 컨테이너에서 실행 중이라면 독자 PC의 준비 상태로 대신 판정하지 않습니다.
- environment_report.md에는 하나의 표로 기록합니다. 확인 기준을 통과한 항목은 Ready,
  실패·기준 미달·미실행 또는 근거가 부족한 항목은 Needs Fix입니다.
- Needs Fix 항목은 오류 또는 미실행 사유와 필요한 조치를 적고, 해당 절에서 해결한 뒤 같은 기준으로 다시 확인합니다.
- 모든 항목이 Ready이고 문서 검증·독자 자가 체크를 마치면 Chapter 6이 완료되며 Chapter 7로 이동합니다.
  이후 장은 이 장에서 준비한 도구를 설치 없이 그대로 사용합니다.
