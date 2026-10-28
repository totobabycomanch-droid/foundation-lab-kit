# 두 웹 실습 시작하기

작업 위치는 ch07/understanding/입니다. Chapter 6에서 만든 ch07/.venv의 Python 3.12를 사용합니다.
외부 패키지 없이 Python 표준 HTTP 서버·sqlite3·unittest와 브라우저 JavaScript로 동작합니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_lab.ps1
```

http://127.0.0.1:8307 을 엽니다. 사용 중인 포트라면 명령에 -Port 8308을 붙이고 주소도 바꿉니다.
서버 종료는 Ctrl+C입니다. 업무 파일은 요청 때 다시 읽으므로 수정 후 화면에서 다시 요청하면 됩니다.
가상환경이 없다면 Chapter 6의 6.2로 돌아갑니다. requirements.txt·Node.js·Docker·Supabase는 이 장에서 준비하지 않습니다.

## AI가 완성할 파일

- transaction_example.py: 실습 1의 실제 주문 실패·중간 확정·전체 취소 비교
- sale_example.py: 실습 2의 판매·재시도·충돌·재고 조건·트랜잭션
- test_examples.py: 실습별 업무 검사. 시작본의 미구현 실패를 실제 검사로 교체하고 이후 기존 검사를 보존합니다.

화면·연결·추적·초기 준비·독립 검사는 제공됩니다. 시작본 501은 업무 구현 전 안내입니다.
업무 코드의 BEGIN·COMMIT·ROLLBACK을 제공 서버가 대신 구현하지 않습니다. 정확한 함수·DB 규약은 AGENTS.md와 시작본 설명을 따릅니다.

## 직접 확인할 사례

실습 1: 초기10·수량1의 독립 DB 두 개에서 실제 주문 저장을 실패시켜 재고9/10·주문0을 비교합니다.
실습 2: 초기5에서 2개 판매 → 같은 요청 재전송 → 내용 변경 충돌 → 새 판매의 2개 판매를 확인합니다.
별도 초기화 후 재고 부족6·정확한 소진5·실제 저장 실패와 같은 요청 재전송도 확인합니다.
재전송은 같은 DB·키·원래 입력을 유지합니다. 비교·초기화·새 요청·새로고침을 같은 행동으로 취급하지 않습니다.
실제 실행 결과 복사 버튼으로 이 탭에서 수집한 내역을 AI에게 전달합니다. 수기 표·로그 해석을 필수로 요구하지 않습니다.

## 검사와 복구

기본은 AI에게 제공 검사와 업무 검사를 실행시키고 한국어 보고를 읽는 방식입니다. 이미 실행했다면 반복하지 않습니다.
AI가 실행하지 못했을 때만 서버 터미널을 유지하고 별도 PowerShell에서 해당 실습의 명령을 실행합니다.

```powershell
& ..\.venv\Scripts\python.exe .\verify_observation.py
& ..\.venv\Scripts\python.exe .\verify_web.py --exercise transaction
& ..\.venv\Scripts\python.exe .\verify_web.py --exercise sale
& ..\.venv\Scripts\python.exe -m unittest -v test_examples.py
```

verify_observation은 제공 기반, verify_web은 현재 업무의 독립 검사입니다. 생성 테스트가 없거나 일부 사례를 빼먹어도 독립 검사는 실행할 수 있습니다.
영어 출력은 그대로 AI에게 전달해 실제 실행 여부·업무 약속·실패·미확인을 한국어로 설명받습니다.
검사는 임시 사본·별도 서버·DB를 사용하며 현재 .lab이나 실행 중인 서버는 변경하지 않습니다.
복구는 현재 코드·결과를 보관한 뒤 _starter/의 해당 업무 파일을 선택해 되돌립니다. 이 경우 기존 AI 구현은 사라집니다.
참고 비교는 사용자가 선택했을 때만 reference/README.md를 따릅니다.

로컬 화면의 HTTP 확인과 순차 재시도·의도적 저장 오류를 다룹니다. 실제 동시 경합·서버 중단·실제 네트워크 응답 유실·운영 ERP의 분산 멱등성은 검증하지 않습니다.
