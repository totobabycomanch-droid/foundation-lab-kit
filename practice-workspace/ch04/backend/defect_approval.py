"""Fixed defect-workspace flow. The learner repairs its company-scoped lookup."""
from . import defect_scope
from .defect_rules import check_permission


def approve_order(store, order_id, user):
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
