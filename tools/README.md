# Foundation Lab Kit 도구

키트 전체의 필수 파일과 생성 부산물 유무를 읽기 전용으로 확인합니다.

```powershell
./tools/verify_foundation_kit.ps1
```

Chapter별 시작 파일은 다음처럼 확인합니다.

```powershell
./tools/verify_practice_chapter.ps1 -Chapter ch08
```

초기화 도구는 기본적으로 대상만 보여 줍니다. 출력된 경로를 확인한 뒤에만 `-Apply`를 붙입니다.

```powershell
./tools/reset_practice_chapter.ps1 -Chapter ch08
./tools/reset_practice_chapter.ps1 -Chapter ch08 -Apply
```

Chapter 5·10·11의 SQL 도구는 데이터베이스에 자동 접속하지 않습니다. 반드시 폐기 가능한 전용 실습 DB에서 `00_initialize_lab.sql`로 표식을 만든 뒤, 같은 Chapter의 `99_reset_lab.sql`을 직접 실행하세요.
