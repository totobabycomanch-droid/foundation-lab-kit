"""학습자가 완성할 판매·재시도 처리."""
from lab_contracts import LabError


def sell(db, request_key, product_code, quantity):
    """성공한 판매번호(int)를 반환하고 실패·거부면 이번 변경을 취소한다.

    stock(prod_code,qty), sales(id,request_key,prod_code,qty)를 사용한다.
    같은 키·같은 상품·수량은 기존 번호를 반환한다. 다른 내용은 LabError(409,...).
    수량은 bool·문자열을 제외한 1~1,000,000의 정수만 허용한다(LabError 422).
    차감 SQL의 재고 조건과 변경 행 수로 부족을 거부한다(LabError 409).
    판매·키·차감을 같은 트랜잭션으로 처리하고, 저장 오류는 취소 후 다시 전달한다.
    db.execute(...).fetchone()/fetchall()은 dict, rowcount/lastrowid는 정수다.
    연결·초기화·표시·HTTP 처리는 제공 기능이다. 업무 트랜잭션은 이 함수가 담당한다.
    """
    raise LabError(501, '원고 7.5의 AI 요청으로 판매·재시도를 먼저 구현하세요.')
