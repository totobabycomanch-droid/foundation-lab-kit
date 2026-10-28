"""학습자가 완성할 주문 저장 실패·트랜잭션 비교."""
from lab_contracts import LabError


def run_transaction(db, quantity, commit_early):
    """준비·확정된 DB에서 재고 차감 뒤 실제 주문 저장을 실패시킨다.

    db는 execute/commit/rollback/in_transaction을 제공하고 조회 행은 dict다.
    stock(prod_code,qty)의 A001을 quantity만큼 차감한다. commit_early=True일
    때만 차감을 중간 확정한다. orders(qty)에 0을 INSERT하면 CHECK 오류가 난다.
    오류 시 rollback한 뒤 실제 sqlite3.IntegrityError를 다시 전달한다.
    BEGIN·COMMIT·ROLLBACK은 이 업무 코드가 담당한다. 초기화·연결 종료는 제공 기능이다.
    """
    raise LabError(501, '원고 7.3의 AI 요청으로 주문 실패 비교를 먼저 구현하세요.')
