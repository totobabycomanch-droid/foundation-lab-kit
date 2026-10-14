# Chapter 9 비교용 기준 예제

이 폴더는 생성 실습이 막혔을 때 독자가 비교하는 자료입니다.
정상 생성·검증 중 AI가 답안으로 읽거나 erp-mini/에 복사하지 않습니다.
파일 구성이나 문법의 일치보다 업무 규칙과 실행 결과를 비교하세요.

1. 고정 검사의 실패 항목에서 현재 상태·요청 행동을 확인합니다.
2. 자신의 domain/order.py에서 검사보다 상태 대입이 앞서는지 확인합니다.
3. order.py의 공통 전이 검사와 자신의 코드를 비교합니다.
4. test_order.py의 재승인 테스트에서 예외 검사와 상태 유지 검사를 비교합니다.
5. 원고의 세 파일 범위 안에서 최소 수정한 뒤 예제·생성 테스트·고정 검사를 다시 실행합니다.

기준 예제 자체를 확인하려면 키트 루트에서 실행합니다.

```powershell
python -B ./practice-workspace/ch09/reference/test_order.py
python -B ./practice-workspace/ch09/checks/test_order_rules.py --order-file ./practice-workspace/ch09/reference/order.py
```

고정 검사는 업무 규칙에서 작성한 기대값으로 30개 상태·행동 조합과 신규 상태,
직접 대입 거부, 주문 간 상태 독립성을 검사합니다. 생성 코드의 전이 표를 기대값으로 사용하지 않습니다.
DB·HTTP·동시 요청·멱등성은 검사 범위 밖입니다. 기준 파일은 초기화 후에도 보존됩니다.
