from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Franchise(Base):
    __tablename__ = "franchise"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deposit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Stock(Base):
    __tablename__ = "current_stock"

    prod_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    stock_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    franchise_id: Mapped[int] = mapped_column(ForeignKey("franchise.id"), nullable=False)
    prod_code: Mapped[str] = mapped_column(ForeignKey("current_stock.prod_code"), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

