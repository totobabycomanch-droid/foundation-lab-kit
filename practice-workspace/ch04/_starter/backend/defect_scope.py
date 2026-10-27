"""Exercise 4 comparison query. Change only this file after tracing the cause."""


def find_order(db, order_id, user):
    return db.execute(
        "SELECT * FROM orders WHERE id = ?", (order_id,)
    ).fetchone()
