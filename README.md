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

## v1.3.11 Chapter 8 재실습

FastAPI·Starlette·httpx2 의존성 조합을 고정하고 테스트 docstring과 단계별 반환값 설명 지침을 보완했습니다.
객체가 아닌 JSON을 HTTP 400으로 거부하는 명세와 참고 API의 앱 테스트도 함께 제공합니다.
새 폴더에 압축을 풀고 가상환경과 의존성을 새로 준비하세요. 이전 실습의 코드·DB·가상환경은 가져오지 않습니다.

## v1.3.12 Chapter 8 이해 중심 실습

개편 원고는 Day 16의 실제 발주 흐름을 이해하는 준비 장입니다.
새 실습은 practice-workspace/ch08/understanding/에서 Python 기본 기능으로 세 사례를 확인합니다.
이전 project/·reference/와 네 단계 지침은 보관 자료로 남겼으며 새 필수 과정에서 사용하지 않습니다.
v1.3.12는 개편 Chapter 8용입니다. 위 v1.3.9~v1.3.11 안내는 이전 원고의 배포 이력입니다.

## v1.3.13 Chapter 5·7 개편 실습

Chapter 5는 두 임시 테이블 SQL 예제로 현재값·이력과 상품·거래 관계를 확인합니다.
ch05/에서 AI에게 SQL 두 개를 요청한 뒤 전용 Supabase SQL Editor에서 전체 실행합니다.
이전 초기화 SQL은 ch05/.archive/sql/로 옮겼으며 새 Core에서 사용하지 않습니다.

Chapter 7은 ch07/understanding/에서 Python 기본 SQLite와 unittest로 부분 저장·롤백,
재고 부족·순차 재시도·키 충돌을 확인합니다. 이전 API 안내는 legacy-api/에 보관했습니다.
Chapter 8은 v1.3.12의 작은 이해 실습을 그대로 사용합니다.

기존 실습 폴더를 덮어쓰지 말고 비어 있는 새 폴더에 압축을 풉니다.
생성 SQL·Python 구현, 실제 DB·가상환경은 시작점에 제공하지 않습니다.

## v1.3.14 Chapter 5 검증 기준 정리

두 SQL을 전체 재실행해 결과가 같은지 확인하고, 코드 검토와 독자가 제공한 실행 결과를 구분합니다.
임시 테이블 자동 정리의 코드 확인과 실제 정리 확인을 구분하며, AI 직접 DB 실행과 별도 정리 조회를
독자의 추가 완료 조건으로 요구하지 않습니다. 실습 범위 밖 항목은 필수 검사의 누락과 구분합니다.
SQL 참고 코드와 다른 Chapter의 실습 내용은 v1.3.13과 같습니다.

## v1.3.15 Chapter 5 직접 조회 실습

위 v1.3.13·v1.3.14 안내는 이전 배포 이력입니다. 이 개정본의 Chapter 5는 ch05_lab의 일반 테이블을 사용합니다.
각 SQL을 실행한 뒤 본문의 SELECT로 직접 조회하며, 데이터는 COMMIT 후에도 남습니다.
재실행은 해당 실습 테이블만 초기화합니다. 새 실행 규칙은 ch05/AGENTS.md와 sql/README.md를 따릅니다.
다른 Chapter는 foundation-kit-v1.3.14 배포본과 동일합니다.

## v1.3.16 Chapter 9 상태 규칙 실습

이 버전은 v1.3.15를 기준으로 공통 보고 규칙과 Chapter 9 지침을 정리했습니다.
AI는 practice-workspace/AGENTS.md의 공통 보고 규칙에 따라 실행 결과와 최신 파일의 근거를 보고합니다.
Chapter 9는 9.4의 단일 주문 예제와 테스트에서 코드 생성·실행을 마칩니다.
9.5 이후는 읽기 구간이며 Payment·Inventory·서버 코드를 추가하지 않습니다.
다른 Chapter의 파일과 실행 코드는 v1.3.15와 같습니다.
