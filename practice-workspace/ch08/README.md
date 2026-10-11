# Chapter 8 — 실제 ERP의 발주 흐름을 이해하는 준비 장

개편 Chapter 8은 작은 Python 예제로 입력 검증과 서버 기준 계산을 확인합니다.
저장과 API는 실제 ERP의 흐름을 읽으며 이해하고 Day 16에서 구현합니다.

## 시작 위치

VS Code에서 `ch08/understanding/` 폴더를 엽니다.
이 폴더의 AGENTS.md와 README.md가 생성 위치·실행 방법을 안내합니다.
Python 3.12가 설치돼 있으면 실행할 수 있으며 외부 패키지 설치는 필요하지 않습니다.

| 위치 | 역할 |
|---|---|
| understanding/ | 개편 원고의 작은 검증·계산 실습 |
| ai_build_rules.md·ai_review_rules.md | 간결한 생성·검토 기준 |
| chapter8_order_spec.md | 작은 실습의 입력·세 대표 결과·확인 범위 |
| project/·reference/·legacy-api/ | 이전 네 단계 API 실습 보관 자료. 개편 필수 실습에 사용하지 않음 |

## 진행

1. 원고의 생성 요청으로 예제와 테스트를 만듭니다.
2. 같은 폴더에서 `python order_example.py`를 실행합니다.
3. AI가 `python -m unittest -v test_order_example.py`로 세 사례를 검증합니다.
4. 정상 5500·조작 단가 제외·수량 0 거부를 확인합니다.

서버 단가 1000은 제공된 예제 값이며 DB 조회 결과가 아닙니다.
계산 결과는 저장된 발주가 아닙니다. 실제 HTTP·DB·동시성 검증은 이번 실습에 포함하지 않습니다.

## 이전 실습과 배포 상태

v1.3.11까지의 공개 키트는 project/에서 네 단계 API를 만드는 이전 원고용입니다.
v1.3.12부터 개편 원고의 understanding/ 실습을 제공합니다. 새 폴더에 풀고 작은 예제를 생성하세요.
이전 결과를 초기화하거나 새 예제로 덮어쓰지 않습니다. 기존 실행 안내는 legacy-api/README.md에 보관했습니다.
