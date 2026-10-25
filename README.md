# Foundation Lab Kit

이 실습 키트의 고정 배포 버전은 `foundation-kit-v1.3.32`입니다.
Chapter 2~3에서는 `reference-app/`을 읽고 테스트하며, Chapter 4~11에서는
`practice-workspace/`의 해당 Chapter 폴더를 열어 실습합니다.
기존 작업을 보존하고 비어 있는 새 폴더에 압축을 풉니다. 실제 `.env`·DB·가상환경은 제공하지 않습니다.

## 최신 점검용 다운로드

- [최신 배포](https://github.com/totobabycomanch-droid/foundation-lab-kit/releases/latest)
- [최신 키트 ZIP](https://github.com/totobabycomanch-droid/foundation-lab-kit/releases/latest/download/foundation-lab-kit-latest.zip)
- [최신 체크섬](https://github.com/totobabycomanch-droid/foundation-lab-kit/releases/latest/download/foundation-lab-kit-latest.sha256)

다운로드 주소는 유지하며 새 배포마다 최신 Release로 연결됩니다. ZIP·체크섬을 같은 Release에서 받으세요.
현재 버전은 루트의 release-manifest.json으로 확인합니다. 기존 실습 폴더에 덮어쓰지 않습니다.

최신 [기초 준비 안내](docs/01A_foundation_lab_setup.md)와 [Chapter 11 원고](docs/11_chapter11.md),
두 문서에서 사용하는 화면 이미지를 함께 제공합니다. 다른 장의 본문은 전자책을 참고합니다.
이 묶음의 문서 범위는 [문서 안내](docs/README.md)를 확인하세요.

## 이번 버전에 포함된 자료

- Chapter 10: 전용 DB 초기화 표식·시작 코드와 `chapter-reference/ch10/`의 비교·복구 코드
- Chapter 11: 관찰 기록 양식과 `chapter-reference/ch11/`의 SQL·API·Vue 참조 코드 및 사용 안내
- 검증 도구: 시작 파일과 Chapter 10·11 참조 파일의 누락 확인

참조 코드는 필수 실습을 대신하지 않습니다. 막힌 단계에서만 비교하며 정상 코드를 덮어쓰지 않습니다.
Chapter 11의 API와 화면 완성 코드는 시작 폴더에 없으며 AI와 직접 작성합니다.
추가 참조 ZIP을 받을 필요 없이 해당 `chapter-reference/` 폴더를 확인하세요.

```powershell
./tools/verify_foundation_kit.ps1
./tools/verify_practice_chapter.ps1 -Chapter ch10
./tools/verify_practice_chapter.ps1 -Chapter ch11
```

검증 도구는 Supabase DB에 접속하지 않습니다. DB·브라우저의 실제 동작은 원고에 따라 직접 확인합니다.
Day 00에서는 이 키트를 개조하지 않고 별도 폴더에 ERP 프로젝트를 준비합니다.

## 이전 버전 이력

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

## v1.3.16~v1.3.17 Chapter 9 상태 규칙 실습

v1.3.16은 공통 보고 규칙과 Chapter 9의 Core 범위를 정리했습니다.
v1.3.17은 tools/verify_ch09_core.ps1의 고정 검사와 ch09/reference/의 비교 예제를 추가합니다.
Chapter 9 코드 생성·실행은 9.4에서 마치며 9.5 이후는 읽기 구간입니다.
다른 Chapter의 실습 파일은 v1.3.15와 같습니다.

## v1.3.18 Chapter 8 독자 검증과 고정 검사

입력 변경 전 예상과 직접 호출 결과를 AI 검토·대표 테스트의 단언문에 연결합니다.
validate_item·calculate_amounts의 공개 규격을 맞추고 tools/verify_ch08_core.ps1로
생성 테스트와 독립된 고정 검사를 함께 실행합니다. 참고 테스트는 입력 제한과 VAT 경계값도 확인합니다.
v1.3.17 기준 다른 Chapter의 실습은 유지합니다. 기존 폴더를 덮어쓰지 말고 새 폴더에 풀어 실습하세요.

## v1.3.19 이전 배포 이력 — 별도 입력 프로그램

원고의 생성 요청으로 예제를 만든 뒤 python order_example.py --interactive로 상품코드·수량·요청 단가를 입력합니다.
서버 단가 1,000원으로 계산하고 잘못된 수량의 거부·정상 재입력·종료를 확인합니다.
사례명·표시 라벨·오류 설명은 한국어로 표시하며 입력·검증된 품목·계산 결과를 구분합니다.
인자 없는 실행은 기존 세 사례를 출력합니다. 이전 생성 파일은 자동 갱신되지 않으므로 새 폴더에서 생성하거나 AI에게 최소 보완을 요청하세요.
다른 Chapter는 v1.3.18과 동일합니다.

## v1.3.20 Chapter 8 Python 대화형 직접 호출

원고와 키트 지침을 맞춰 수량 -3·0의 ValueError와 정상값 수정, 요청 단가 100원·10원 제외를
>>>에서 직접 확인합니다. 참고 예제의 별도 입력 모드와 관련 구현 요구를 제거했습니다.
기본 실행은 세 사례만 출력하며 import는 입력을 기다리지 않습니다. 다른 Chapter는 v1.3.19와 같습니다.

## v1.3.21 Chapter 8 프롬프트와 검토 부담 정리

관찰 기록 제출 없이 예제와 테스트를 검토합니다. 예상과 다른 결과나 오류가 있을 때만 해당 출력을 전달합니다.
검색 주석·대표 테스트 읽기 표시·완료 보고 형식은 키트 지침에서 관리합니다.
공개 함수·계산 규칙·참고 구현·고정 검사와 다른 Chapter는 v1.3.20과 같습니다.

## v1.3.22 Chapter 5 검사 보강

현재값·이력 실습은 입고와 출고의 순서별 상품·수량·사유까지 검사합니다.
상품·거래 실습은 삭제 차단 기록이 정확히 한 행인지 확인합니다.
두 실습의 조회 결과와 자동 검사 코드는 나누어 검토합니다.
다른 Chapter의 실습 파일은 v1.3.21과 같습니다. 기존 작업 폴더를 덮어쓰지 말고 새 폴더에 압축을 푸세요.
