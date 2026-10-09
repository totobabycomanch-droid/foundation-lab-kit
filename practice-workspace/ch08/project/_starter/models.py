from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    prod_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    purchase_order_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    corp_id: Mapped[str] = mapped_column(String(50), nullable=False)
    partner_id: Mapped[str] = mapped_column(String(50), nullable=False)
    dept_code: Mapped[str] = mapped_column(String(20), nullable=False)
    emp_code: Mapped[str] = mapped_column(String(20), nullable=False)
    delivery_code: Mapped[int] = mapped_column(Integer, nullable=False)
    is_vat: Mapped[str] = mapped_column(String(1), nullable=False)
    order_status: Mapped[str] = mapped_column(String(2), nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class PurchaseOrderDetail(Base):
    __tablename__ = "purchase_order_details"
    __table_args__ = (
        UniqueConstraint("purchase_order_no", "prod_code", name="uq_order_product"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_order_no: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.purchase_order_no"), nullable=False
    )
    prod_code: Mapped[str] = mapped_column(String(50), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    net_price: Mapped[int] = mapped_column(Integer, nullable=False)
    vat: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_order_no: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.purchase_order_no"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    detail_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
