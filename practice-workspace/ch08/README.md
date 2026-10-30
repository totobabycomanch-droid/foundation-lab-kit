# Chapter 8 — 화면에서 발주 검증·계산 확인하기

현재 필수 실습은 understanding/입니다. 실행·검사·복구는 [실행 안내](understanding/README.md)를 따릅니다.
Python 3.12 이상·표준 라이브러리·브라우저를 사용하고 외부 패키지는 설치하지 않습니다.
제공 화면과 관찰 서버는 실제 업무 함수를 호출하며 독자는 업무 코드와 테스트 두 파일을 AI와 완성합니다.
정상 계산·요청 단가 조작·서버 기준값 변경·수량 거부·VAT 경계값을 비교합니다.

명세는 chapter8_order_spec.md, 생성·검토 기준은 ai_build_rules.md와 ai_review_rules.md입니다.
실제 ERP의 단가 조회·마스터·상세·감사 원자 저장은 Day 16에서 이어갑니다.
로컬 관찰 서버를 사용했다는 사실을 실제 ERP API·DB 검증으로 표현하지 않습니다.

project/·reference/·legacy-api/는 이전 API 실습 자료이며 이번 실습에 가져오지 않습니다.
기존 학습자 파일은 조사 후 보완하며 시작본·참고 완성본으로 덮어쓰지 않습니다.
