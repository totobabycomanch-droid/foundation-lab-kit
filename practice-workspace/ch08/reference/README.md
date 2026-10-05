# Chapter 8 단계별 참고 구현

AI가 만든 코드를 수정해도 같은 오류가 반복될 때 현재 단계의 구현과 비교합니다.
각 폴더는 해당 단계까지 완성한 누적 코드이며, 다음 단계의 코드는 포함하지 않습니다.
참고 파일을 이 폴더에서 직접 실행하지 말고 실습 중인 `ch08/project/`에서 확인합니다.

| 막힌 단계 | 비교할 파일 | 복구 후 확인 |
|---|---|---|
| 8.2 | [요청 검증](8.2/services/franchise_order.py), [요청 검증 테스트](8.2/tests/test_change.py) | `python -m pytest -q tests/test_change.py` |
| 8.3 | [요청 검증·업무 판단](8.3/services/franchise_order.py), [누적 테스트](8.3/tests/test_change.py) | `python -m pytest -q tests/test_change.py` |
| 8.4 | [저장](8.4/repositories/franchise_order.py), [저장 테스트](8.4/tests/test_persist.py) | 판단·저장 테스트 모두 실행 |
| 8.5 | [API 연결](8.5/routers/franchise_order.py), [앱 등록](8.5/main.py) | OpenAPI 등록과 원고의 실제 발주 확인 |

1. 수정하기 전 현재 단계의 대상 파일을 별도 폴더에 복사해 보관합니다.
2. 오류가 난 파일과 같은 단계의 참고 파일을 비교하고, AI에게 차이와 최소 수정안을 요청합니다.
3. 여전히 해결되지 않으면 현재 단계의 대상 파일만 참고 파일로 교체합니다. 폴더 전체를 덮어쓰지 않습니다.
4. 같은 명령을 다시 실행하고, 어떤 차이가 오류를 일으켰는지 확인한 뒤 다음 단계로 갑니다.

이전 단계의 파일에도 오류가 있으면 해당 단계의 참고 구현으로 먼저 복구합니다.
`database.py`, `models.py`, `practice_db.py`, 환경 설정과 `__init__.py`는 교체하지 않습니다.
8.5의 HTTP 요청을 다시 보내기 전에는 원고 안내대로 DB 값을 먼저 확인합니다.
정상 요청이 이미 저장됐다면 복구 확인을 위해 같은 발주를 다시 보내지 않습니다.
