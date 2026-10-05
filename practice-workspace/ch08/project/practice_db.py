from __future__ import annotations

import sys

from sqlalchemy import func, select

from database import SessionLocal, engine
from models import Base, Franchise, Order, Stock


def require_local_sqlite() -> None:
    if engine.dialect.name != "sqlite":
        raise RuntimeError("Chapter 8 Core 실습은 로컬 SQLite에서만 실행합니다.")


def prepare() -> None:
    """실습 테이블과 없는 기초 데이터만 준비합니다."""
    require_local_sqlite()
    Base.metadata.create_all(engine)

    with SessionLocal.begin() as db:
        if db.get(Stock, "A001") is None:
            db.add(Stock(prod_code="A001", stock_qty=100, unit_price=1000))
        if db.get(Franchise, 1) is None:
            db.add(Franchise(id=1, deposit=50000))

    print("로컬 DB 준비 완료 (기존 데이터 유지)")


def show() -> None:
    """A001 재고, 가맹점 1 예치금과 전체 주문 건수를 출력합니다."""
    require_local_sqlite()

    with SessionLocal() as db:
        stock = db.get(Stock, "A001")
        franchise = db.get(Franchise, 1)
        if stock is None or franchise is None:
            raise RuntimeError("먼저 'python practice_db.py prepare'를 실행하세요.")

        order_count = db.scalar(select(func.count()).select_from(Order))
        print(
            f"재고={stock.stock_qty} "
            f"예치금={franchise.deposit} "
            f"주문={order_count}"
        )


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"prepare", "show"}:
        raise SystemExit("사용법: python practice_db.py [prepare|show]")

    if sys.argv[1] == "prepare":
        prepare()
    else:
        show()


if __name__ == "__main__":
    main()
