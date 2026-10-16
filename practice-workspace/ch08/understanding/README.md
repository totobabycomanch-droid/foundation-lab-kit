# 작은 발주 예제 시작 폴더

AI가 order_example.py와 test_order_example.py를 생성할 위치입니다.
입력은 품목 한 건이며 정상 5500·조작 단가 제외·수량 0 거부를 확인합니다.

## 실행 환경

VS Code에서 이 understanding/ 폴더를 열고 PowerShell 터미널을 사용합니다.
Python 3.12 설치를 확인합니다. 별도 가상환경이나 패키지 설치는 필요하지 않습니다.

```powershell
Get-Location
python --version
```

현재 위치가 같은 키트의 ch08/understanding인지 확인합니다.
설치 문제가 있으면 기초 환경 준비 안내에서 Python 설치를 확인합니다.
AI에게도 이 폴더의 절대 경로를 보고하도록 합니다.

## 생성 후 실행

원고의 생성 요청을 전달합니다. AI가 계획만 보고했다면 범위를 확인해 승인한 뒤 구현 완료를 기다립니다.

```powershell
python order_example.py
```

정상 요청·단가 1원 조작 요청은 모두 5000·500·5500이어야 하며 수량 0은 거부돼야 합니다.
서버 단가 1000은 제공된 값이며 DB 조회 결과가 아닙니다. 계산만 수행하고 저장하지 않습니다.
AI는 다음 명령으로 입력·단언문·실행 결과를 확인합니다.

```powershell
python -m unittest -v test_order_example.py
```

chapter8_order_spec.md의 공개 함수는 validate_item(payload)와
calculate_amounts(item, *, server_unit_price, is_vat)입니다. 검증 결과는 prod_code·qty,
계산 결과는 unit_price·supply_amount·vat_amount·total_amount 필드를 사용하며 잘못된 값은 ValueError로 거부합니다.
내부 구현은 자유롭게 정합니다. 이전에 생성한 함수의 이름이나 반환 형식이 다르면 공개 규격에 맞춥니다.

독자가 직접 입력을 바꿔 예상·관찰한 결과와 테스트의 실제 입력·단언문을 확인합니다.
공백 제거·수량 제한·VAT 구분·104/105/106원 경계값과 서버 값 검증도 검사합니다.
생성 테스트와 별도로 checks/test_order_rules.py가 고정된 업무 기대값으로 동작을 검사합니다.
현재 understanding/ 위치에서 실행합니다.

```powershell
../../../tools/verify_ch08_core.ps1
```

이 명령은 생성 테스트와 고정 검사를 모두 실행합니다. PASS를 확인하고, NOT RUN이면 생성 파일·실행 위치를,
FAIL이면 실패한 입력·기대값·실제 결과를 확인합니다. checks/는 수정하지 않습니다.
생성 테스트 누락이나 수량 0 이후의 계산 호출 여부는 코드·단언문과 함께 별도로 확인합니다.
DB·HTTP·동시성은 검증 범위 밖입니다.

## 막혔을 때

- 파일 없음: AI가 보고한 절대 경로와 Get-Location을 대조합니다. 다른 폴더에서 재생성하지 않습니다.
- 구현 미완료: 계획 보고와 구현 완료를 구분하고 승인 후 실행합니다.
- 결과 불일치: 실제 출력과 오류를 AI에게 전달해 원인과 최소 수정 범위를 요청합니다.
- 이해가 어려움: test_order_example.py에서 AI가 지정한 테스트 이름과 docstring·검사 코드를 읽습니다.

reference/에는 검증한 참고 예제가 있습니다. 막혔을 때 독자가 읽는 자료이며 AI 생성 답안으로 쓰지 않습니다.
실제 발주 API를 만드는 project/와 이전 키트 지침을 이번 예제에 적용하지 않습니다.
