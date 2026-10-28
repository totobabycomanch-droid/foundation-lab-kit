"""학습자가 완성할 상품 선택 목록·예전 거래 조회."""
from .contracts import MovementError


def read_relationships(db):
    """{'selection': [상품 행], 'trades': [거래·상품 연결 행]}을 반환한다.

    selection은 code,name을 가진 취급 중 상품 목록이다.
    trades는 trade_no,code,name,quantity,is_deleted를 가진 JOIN 결과다.
    예전 거래에는 취급 중 상품만 고르는 조건을 적용하지 않는다.
    SQL은 제공 db.execute(...).fetchall()로 실행한다. 정렬은 code/trade_no 순이다.
    """
    raise MovementError(501, "5.4의 AI 구현 요청으로 목록·거래 조회를 먼저 완성하세요.")
