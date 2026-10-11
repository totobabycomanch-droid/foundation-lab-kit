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

Chapter 5·10·11의 SQL은 폐기 가능한 전용 실습 DB에서 해당 장의 초기화 절차를 따릅니다.
