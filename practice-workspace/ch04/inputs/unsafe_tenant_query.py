"""Chapter 4 검토용 위험 코드입니다. 이 파일은 수정하지 않습니다."""


def list_orders(db, corp_id: str):
    return db.execute(
        "SELECT order_id, status FROM orders WHERE corp_id = :corp_id",
        {"corp_id": corp_id},
    )

