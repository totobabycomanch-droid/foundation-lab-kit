"""선택 비교용 선택 목록과 예전 거래 조회."""


def read_relationships(db):
    selection = db.execute('SELECT code, name FROM lab_product WHERE is_deleted = 0 ORDER BY code').fetchall()
    trades = db.execute('''SELECT t.trade_no, p.code, p.name, t.quantity, p.is_deleted
        FROM lab_trade AS t JOIN lab_product AS p ON p.id = t.product_id ORDER BY t.trade_no''').fetchall()
    return {'selection': selection, 'trades': trades}
