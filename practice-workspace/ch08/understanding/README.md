# Chapter 8 — 화면에서 발주 입력과 계산 확인하기

## 실행 환경과 위치

VS Code에서 foundation-lab-kit/practice-workspace/ch08/understanding/을 엽니다.
PowerShell에서 Python 3.12 이상인지 확인합니다. 외부 패키지·Node.js·Docker·DB 준비는 필요하지 않습니다.
Chapter 7의 .venv와 이전 API 실습 requirements.txt를 사용하지 않습니다.

```powershell
Get-Location
python --version
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_lab.ps1
```

브라우저에서 http://127.0.0.1:8308을 엽니다. 포트 충돌 시 -Port 8309를 붙이고 주소도 바꿉니다.
실행 터미널의 Ctrl+C로 종료합니다. 실행 정책은 영구 변경되지 않습니다.
코드를 수정한 뒤 화면에서 다시 실행하면 최신 파일을 읽습니다.
시작본은 501 미구현 안내가 정상이며 AI와 업무 코드·테스트를 완성한 뒤 다시 실행합니다.

## 실습 흐름

1. 이 폴더의 AGENTS.md와 연결 명세를 AI가 조사하고 계획을 보고하게 합니다.
2. order_example.py와 test_order_example.py 두 파일만 구현합니다. 기존 작업은 조사 후 필요한 부분만 보완합니다.
3. 화면에서 정상·요청 단가 조작·서버 기준값 변경·수량 거부와 복구·VAT를 비교합니다.
4. 실행 전에 예상하고 실제 입력·검증 반환값·계산 인자·반환값 또는 예외·미실행을 읽습니다.
5. 'AI 검증용 실행 결과 복사'로 관찰 내역을 복사하고 AI에게 코드·검사를 대조하게 합니다.
6. 대표 검증·계산 코드와 테스트의 단언문을 한 곳씩 읽습니다. 실패·미실행·누락은 해결 후 완료합니다.

새로고침하면 관찰 내역은 사라집니다. '입력과 관찰 초기화'는 기본 입력으로 돌아가고 표시와 내역을 비웁니다.
DB와 저장 데이터는 없습니다. 서버 기준값은 실습용이며 계산 결과는 저장된 발주가 아닙니다.
화면에서 설정한 서버 단가는 품목 요청 단가와 별도 인자로 전달됩니다. 실제 ERP의 가격 보안을 구현한 기능이 아닙니다.

## 검사와 보호 범위

같은 Python으로 생성 테스트·고정 업무 검사·제공 연결 검사를 실행합니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ../../../tools/verify_ch08_core.ps1
```

NOT RUN은 업무 파일·테스트 누락, FAIL은 출력에 표시된 실패 입력과 오류부터 확인합니다.
checks/의 기대값을 변경하거나 제공 화면·서버·verify_web.py·지침을 수정해 통과시키지 않습니다.
실제 ERP API·DB 조회·저장·롤백·동시 요청은 범위 밖입니다. 로컬 HTTP 검사와 구분합니다.

## 파일과 공개 규격

- order_example.py: validate_item(payload), calculate_amounts(item, *, server_unit_price, is_vat).
- test_order_example.py: AI와 작성할 업무 테스트. 미구현 시작 테스트를 실제 검사로 바꿉니다.
- 검증 반환값: prod_code·qty만. 계산 반환값: unit_price·supply_amount·vat_amount·total_amount.
- 잘못된 입력·서버 단가·VAT 구분은 ValueError로 거부합니다. 내부 구현은 자유롭게 정합니다.
- frontend/·web_server.py·start_lab.ps1·verify_web.py·checks/: 읽기 전용 제공 기능.
- _starter/: 미구현 시작본. reference/: 막혔을 때 독자가 읽는 참고 자료이며 AI 생성 답안으로 사용하지 않습니다.
- project/·상위 reference/·legacy-api/: 이전 API 자료. 이번 필수 실습에 적용하지 않습니다.

## 막혔을 때와 선택 직접 호출

501은 미구현, 400은 업무 함수의 입력 거부, 500은 파일·문법·반환 형식 등의 실행 오류입니다.
정상 수량으로 다시 실행하면 복구돼야 하며 오류 화면의 이전 금액을 정상 결과로 읽지 않습니다.
파일 누락은 AI 보고 경로와 Get-Location을 대조하고, 서버 연결 실패는 실행 터미널과 포트를 확인합니다.
생성 테스트 실패만 조사할 때 python -B -m unittest -v test_order_example.py를 사용합니다.
선택으로 python에서 공개 함수를 직접 호출할 수 있습니다. 종료는 exit()이며 코드 변경 뒤에는 새 Python에서 호출합니다.
