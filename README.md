# Foundation Lab Kit

Chapter 2~3에서는 `reference-app/`을 읽고 테스트하며, Chapter 4~11에서는
`practice-workspace/`의 해당 Chapter 폴더만 수정합니다.

```powershell
./tools/verify_foundation_kit.ps1
```

Day 00에서는 이 키트를 개조하지 않고 별도 폴더에 ERP 프로젝트를 준비합니다.


## v1.3.9 Chapter 8

이 버전은 발주 마스터·상세·감사와 VAT 계산을 사용하는 개정 Chapter 8용입니다.
v1.3.8의 재고·예치금 실습과 모델·요청 규약이 다릅니다. 기존 작업 폴더를 덮어쓰지 말고
새 폴더에 압축을 풀어 ch08/.venv를 준비하세요. 이전 chapter8.db는 가져오지 않습니다.
project/는 시작 파일만 제공하며 구현과 테스트는 원고의 AI 프롬프트로 생성합니다.
막힌 경우에만 ch08/reference/의 현재 단계 참고 구현을 사용하세요.

## v1.3.10 Chapter 8 간결한 AI 실습

공통 생성·검증 지침과 단계별 발주 업무 명세를 포함합니다. 개정 원고의 짧은 요청으로
요청 검증·업무 판단·저장·API 연결을 차례로 구현합니다. 보충 ZIP은 필요하지 않습니다.
새 폴더에 키트를 풀고 실습하세요. 시작 project에는 완성 구현·테스트·DB·가상환경이 없습니다.
기존 v1.3.9의 모델·공개 이름·참고 구현은 유지하며 다른 Chapter의 내용은 변경하지 않았습니다.
