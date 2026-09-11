# Chapter 3 AI 답변 교차 검증 작업 공간

AI 도구 하나만 사용한다면 이 폴더를 사용하지 않아도 된다. 원고의 Core 경로에 따라 예상
판정과 다른 행만 새 대화에 붙여 넣어 검증한다.

둘 이상의 저장소 접근형 AI 도구를 사용할 수 있다면 다음 선택 경로를 진행한다. Codex와
Claude는 AI A와 AI B의 예시이며 다른 도구를 사용해도 된다.

1. AI A는 다른 판정과 `expected-verdict.md`를 읽지 않고 소스를 조사해
   `ai-a-verdict.md`를 작성한다.
2. AI B도 같은 조건에서 독립적으로 `ai-b-verdict.md`를 작성한다.
3. 두 파일이 모두 완성되면 AI A 또는 AI B가 두 판정, `expected-verdict.md`와 실제 소스를
   비교해 `comparison.md`를 작성한다.
4. 독자는 `comparison.md`가 가리킨 핵심 파일과 코드만 직접 확인한다.

각 판정은 `ai-verdict-template.md`, 비교 결과는 `comparison-template.md` 형식을 따른다.
결과 파일은 독자의 로컬 기록이며 키트 배포 원본에는 포함하지 않는다.
