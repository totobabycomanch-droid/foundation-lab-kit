# 파일 경로: project/tests/test_persist.py
# 인메모리 SQLite에서 저장 계획의 원자성을 검사합니다 (파일 DB와 서버는 사용하지 않습니다)
import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base, Franchise, Order, Stock
from repositories.franchise_order import FranchiseOrderConflict, persist_franchise_order
from services.franchise_order import FranchiseOrderPlan


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autocommit=False, autoflush=False)()
    with session.begin():
        session.add(Stock(prod_code="A001", stock_qty=100, unit_price=1000))
        session.add(Franchise(id=1, deposit=50000))
    yield session
    session.close()


def plan(qty=5, total_price=5000):
    return FranchiseOrderPlan(
        franchise_id=1, prod_code="A001", qty=qty, total_price=total_price, order_status=10
    )


def snapshot(db):
    with db.begin():
        stock = db.get(Stock, "A001").stock_qty
        deposit = db.get(Franchise, 1).deposit
        orders = db.scalar(select(func.count()).select_from(Order))
    return stock, deposit, orders


def test_persist_saves_all_three_changes(db):
    order_id = persist_franchise_order(plan(), db)
    with db.begin():
        saved = db.get(Order, order_id)
        assert (saved.franchise_id, saved.prod_code, saved.qty, saved.status) == (1, "A001", 5, 10)
    assert snapshot(db) == (95, 45000, 1)


def test_stock_shortage_changes_nothing(db):
    with pytest.raises(FranchiseOrderConflict):
        persist_franchise_order(plan(qty=101), db)
    assert snapshot(db) == (100, 50000, 0)


def test_deposit_shortage_rolls_back_stock_update(db):
    # 재고 차감은 먼저 성공하지만, 예치금 조건이 맞지 않으면 재고도 원래대로 돌아와야 합니다
    with pytest.raises(FranchiseOrderConflict):
        persist_franchise_order(plan(total_price=50001), db)
    assert snapshot(db) == (100, 50000, 0)


def test_order_insert_failure_rolls_back_both_deductions(db):
    # 두 차감이 실행된 뒤 실제 DB의 주문 INSERT를 실패시킵니다.
    with db.begin():
        db.execute(text("""
            CREATE TRIGGER reject_order_insert BEFORE INSERT ON orders
            WHEN (SELECT stock_qty FROM current_stock WHERE prod_code = 'A001') = 95
             AND (SELECT deposit FROM franchise WHERE id = 1) = 45000
            BEGIN
                SELECT RAISE(ABORT, 'forced order insert failure');
            END
        """))
    with pytest.raises(IntegrityError, match="forced order insert failure"):
        persist_franchise_order(plan(), db)
    assert snapshot(db) == (100, 50000, 0)
