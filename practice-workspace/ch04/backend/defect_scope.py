"""Exercise 4 comparison query. Change only this file after tracing the cause."""


def find_order(db, order_id, user):
    """결함 실습의 승인 대상 조회를 담당하며, 조회 행 또는 None을 반환한다.

    db는 진행 중인 트랜잭션의 연결이고, user는 서버가 확인한 사용자다.
    조회 조건과 user의 정보가 어떻게 연결되는지 실제 SQL에서 확인한다.
    이 함수 자체는 발주 상태나 승인 처리 횟수를 바꾸지 않는다.
    """
    return db.execute(
        "SELECT * FROM orders WHERE id = ?", (order_id,)
    ).fetchone()
