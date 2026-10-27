"""Fixed defect-workspace flow. The learner repairs its company-scoped lookup."""
from . import defect_scope
from .defect_rules import check_permission


def approve_order(store, order_id, user):
    """결함 공간의 대상 조회 → 역할·상태 판단 → 승인 저장을 연결한다.

    store는 이 공간의 저장소이고, user는 서버가 확인한 사용자다.
    대상이 없으면 None, 성공하면 갱신된 발주를 반환한다. 판단에서 예외가
    발생하면 저장하지 않는다. 조회한 행의 회사로 갱신하므로 접근 가능한
    대상을 찾았는지는 앞선 조회 조건에서 확인해야 한다.
    """
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = defect_scope.find_order(db, order_id, user)
        if row is None:
            return None
        order = dict(row)
        check_permission(user, order)
        # This targets the row obtained above; its company is not proof of permission.
        changed = db.execute(
            """UPDATE orders SET status = 'APPROVED', approval_count = approval_count + 1
               WHERE id = ? AND corp_id = ? AND status = ? AND approval_count = ?""",
            (order_id, order["corp_id"], order["status"], order["approval_count"]),
        )
        if changed.rowcount != 1:
            raise RuntimeError("Order changed before approval")
        return dict(db.execute(
            "SELECT * FROM orders WHERE id = ? AND corp_id = ?", (order_id, order["corp_id"])
        ).fetchone())
