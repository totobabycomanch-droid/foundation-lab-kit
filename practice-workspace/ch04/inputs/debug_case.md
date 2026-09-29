# 디버깅 사례

가맹점 사용자가 발주 목록 화면을 열면 응답은 HTTP 200이지만 다른 가맹점의 발주가 섞여 보인다.
화면은 요청 쿼리 문자열의 `corp_id`를 그대로 API에 전달한다. API는 이 요청값을
`list_orders(db, corp_id)`에 전달하며, 인증 토큰의 소속 회사와 일치하는지 확인하지 않는다.

증상, 요청 Event, API의 Change, DB 조회 Persistence 순서로 근거를 추적한다.
