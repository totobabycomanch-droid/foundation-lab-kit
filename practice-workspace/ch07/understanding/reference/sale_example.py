"""선택 비교용 판매 처리. 기본 생성·검증에서는 읽지 않는다."""
from lab_contracts import LabError


def sell(db, request_key, product_code, quantity):
    """동일 요청은 재사용하고 신규 판매는 조건부 차감과 함께 확정한다."""
    if not isinstance(request_key,str) or not request_key.strip() or type(quantity) is not int or not 1<=quantity<=1000000:
        raise LabError(422,'입력값을 확인하세요.')
    try:
        db.execute('BEGIN')
        previous=db.execute('SELECT id,prod_code,qty FROM sales WHERE request_key=?',(request_key,)).fetchone()
        if previous:
            if (previous['prod_code'],previous['qty'])!=(product_code,quantity):
                raise LabError(409,'같은 요청 키의 상품 또는 수량이 다릅니다.')
            db.commit()
            return previous['id']
        changed=db.execute('UPDATE stock SET qty=qty-? WHERE prod_code=? AND qty>=?',(quantity,product_code,quantity)).rowcount
        if changed!=1:
            raise LabError(409,'판매 가능한 재고가 부족합니다.')
        number=db.execute('INSERT INTO sales(request_key,prod_code,qty) VALUES (?,?,?)',(request_key,product_code,quantity)).lastrowid
        db.commit()
        return number
    except Exception:
        db.rollback()
        raise
