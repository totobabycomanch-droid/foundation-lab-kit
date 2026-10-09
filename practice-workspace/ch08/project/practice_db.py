from __future__ import annotations

import sys

from sqlalchemy import func, select

from database import SessionLocal, engine
from models import AuditLog, Base, Product, PurchaseOrder, PurchaseOrderDetail


def require_local_sqlite() -> None:
    if engine.dialect.name != "sqlite":
        raise RuntimeError("Chapter 8 Core 실습은 로컬 SQLite에서만 실행합니다.")


def prepare() -> None:
    """실습 테이블과 없는 기초 상품만 준비합니다."""
    require_local_sqlite()
    Base.metadata.create_all(engine)

    with SessionLocal.begin() as db:
        if db.get(Product, "A001") is None:
            db.add(Product(prod_code="A001", unit_price=1000, is_active=True))

    print("로컬 DB 준비 완료 (기존 데이터 유지)")


def show() -> None:
    """상품과 발주 마스터·상세·감사 건수를 출력합니다."""
    require_local_sqlite()

    with SessionLocal() as db:
        product = db.get(Product, "A001")
        if product is None:
            raise RuntimeError("먼저 'python practice_db.py prepare'를 실행하세요.")

        order_count = db.scalar(select(func.count()).select_from(PurchaseOrder))
        detail_count = db.scalar(select(func.count()).select_from(PurchaseOrderDetail))
        audit_count = db.scalar(select(func.count()).select_from(AuditLog))
        print(
            f"상품=A001 단가={product.unit_price} 사용={product.is_active} "
            f"마스터={order_count} 상세={detail_count} 감사={audit_count}"
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
