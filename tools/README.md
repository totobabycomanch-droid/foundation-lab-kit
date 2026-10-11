# Foundation Lab Kit 도구

키트 전체와 Chapter별 시작 문서를 읽기 전용으로 확인합니다.
VS Code의 PowerShell 터미널에서 키트 루트를 현재 위치로 사용합니다.

```powershell
./tools/verify_foundation_kit.ps1
./tools/verify_practice_chapter.ps1 -Chapter ch08
```

Chapter 8 정적 검사는 understanding/의 지침·명세·참고 파일을 확인합니다.
생성된 코드의 동작을 대신 검증하지는 않습니다.
작은 예제가 생성된 뒤 다음 도구로 테스트를 실행할 수 있습니다. 본문에서 별도 실행할 필수 과제는 아닙니다.

```powershell
./tools/verify_ch08_core.ps1
```

Python 실행 파일을 따로 지정하려면 -PythonExecutable에 경로를 전달합니다.
DB 저장·롤백·HTTP·동시성 검증은 이 도구의 범위 밖입니다.
verify_ch08_legacy_api.ps1는 이전 API 실습의 보관 도구이며 새 Chapter 8에서 사용하지 않습니다.

초기화는 기본적으로 대상만 보여 줍니다. Chapter 8은 understanding/의 생성 파일 두 개만 대상입니다.
이전 project/의 코드·DB와 참고 파일은 보존합니다.

```powershell
./tools/reset_practice_chapter.ps1 -Chapter ch08
# 출력된 경로를 확인하고 초기화가 필요할 때만 실행합니다.
./tools/reset_practice_chapter.ps1 -Chapter ch08 -Apply
```

Chapter 10·11의 SQL은 폐기 가능한 전용 실습 DB에서 해당 장의 초기화 절차를 따릅니다.

## Chapter 5 SQL 예제

정적 검사: `./tools/verify_practice_chapter.ps1 -Chapter ch05`
ch05/의 지침과 참고 SQL 두 개를 확인합니다. 생성 SQL은 시작점에 없어도 정상입니다.
이 도구는 DB에 접속하지 않으므로 실제 SQL 실행은 NOT RUN으로 표시합니다.
AI가 만든 sql/ 파일 전체를 전용 Supabase SQL Editor에서 실행하고 실제 조회 결과를 확인합니다.
새 예제는 임시 테이블을 사용합니다. 이전 초기화 SQL은 ch05/.archive/sql/에 보관하며 새 Core에서 실행하지 않습니다.

## Chapter 7 개편 실습

정적 검사: `./tools/verify_practice_chapter.ps1 -Chapter ch07`
생성 후 테스트: `./tools/verify_ch07_core.ps1`
두 도구 모두 키트 루트의 PowerShell 터미널에서 실행합니다.
테스트 도구는 생성 대상 세 파일의 존재와 unittest 실행을 확인하며, 0개 테스트는 실패로 처리합니다.
필수 DB 상태의 단언문은 AI 리뷰에서 따로 확인합니다. 도구 통과가 실제 동시 요청 검증은 아닙니다.
초기화는 `./tools/reset_practice_chapter.ps1 -Chapter ch07`로 대상부터 확인합니다.
`-Apply`는 understanding/의 생성 파일 세 개만 제거합니다. 이전 API 파일·DB·참고 자료는 보존합니다.
메모리 DB 예제는 매 실행마다 새로 시작하므로 일반적인 재실행에 초기화는 필요하지 않습니다.
