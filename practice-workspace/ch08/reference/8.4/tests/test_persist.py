"""8.4 저장 테스트. 인메모리 SQLite만 사용한다(파일 DB·서버 없음)."""

from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from models import AuditLog, Base, Product, PurchaseOrder, PurchaseOrderDetail
from repositories.franchise_order import persist_franchise_order
from services.franchise_order import (
    BranchOrderEvent,
    BranchOrderItemEvent,
    ProductSnapshot,
    decide_franchise_order,
)


class InjectedFailure(Exception):
    pass


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as s, s.begin():
        s.add_all(
            [
                Product(prod_code="A001", unit_price=1000, is_active=True),
                Product(prod_code="B001", unit_price=200, is_active=True),
            ]
        )
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine):
    with Session(engine) as session:
        yield session


def make_plan(items=(("A001", 5),)):
    products = {
        "A001": ProductSnapshot("A001", 1000, True),
        "B001": ProductSnapshot("B001", 200, True),
    }
    order_event = BranchOrderEvent(
        dept_code="D01",
        emp_code="E01",
        delivery_code=1,
        is_vat="2",
        details=tuple(BranchOrderItemEvent(code, qty) for code, qty in items),
    )
    return decide_franchise_order(order_event, products=products)


def counts(engine):
    """새 세션으로 마스터·상세·감사 건수를 센다."""
    with Session(engine) as s:
        return tuple(
            s.scalar(select(func.count()).select_from(model))
            for model in (PurchaseOrder, PurchaseOrderDetail, AuditLog)
        )


def product_rows(engine):
    with Session(engine) as s:
        return [
            (p.prod_code, p.unit_price, p.is_active)
            for p in s.scalars(select(Product).order_by(Product.prod_code))
        ]


@contextmanager
def fail_on_insert(engine, table, attempts, fail_if_param=None, completed=None):
    """테스트 전용: table INSERT가 DB로 전달되기 직전에 기록하고 예외를 일으킨다.

    fail_if_param이 있으면 그 문자열이 INSERT 파라미터에 있을 때만 실패시킨다.
    completed 목록을 주면 DB 커서 실행이 끝난 INSERT의 파라미터를 기록한다.
    테스트가 실패해도 finally에서 리스너를 반드시 제거한다.
    """
    prefix = f"INSERT INTO {table}".upper()

    def hook(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith(prefix):
            attempts.append((statement, parameters, executemany))
            if fail_if_param is None or fail_if_param in repr(parameters):
                raise InjectedFailure(table)

    def done(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith(prefix):
            completed.append(parameters)

    event.listen(engine, "before_cursor_execute", hook)
    if completed is not None:
        event.listen(engine, "after_cursor_execute", done)
    try:
        yield
    finally:
        event.remove(engine, "before_cursor_execute", hook)
        assert not event.contains(engine, "before_cursor_execute", hook)
        if completed is not None:
            event.remove(engine, "after_cursor_execute", done)
            assert not event.contains(engine, "after_cursor_execute", done)


def test_persist_single_order(engine, db):
    assert counts(engine) == (0, 0, 0)

    order_no = persist_franchise_order(make_plan(), db)

    assert counts(engine) == (1, 1, 1)
    with Session(engine) as s:
        order = s.get(PurchaseOrder, order_no)
        assert order.total_amount == 5500
        detail = s.scalars(select(PurchaseOrderDetail)).one()
        assert detail.purchase_order_no == order_no
        assert (detail.unit_price, detail.net_price, detail.vat, detail.total_amount) == (
            1000, 5000, 500, 5500,
        )
        audit = s.scalars(select(AuditLog)).one()
        assert (audit.purchase_order_no, audit.action) == (order_no, "INSERT")
        assert (audit.detail_count, audit.total_amount) == (1, 5500)
    assert product_rows(engine) == [("A001", 1000, True), ("B001", 200, True)]


def test_persist_multiple_details(engine, db):
    plan = make_plan([("A001", 5), ("B001", 2)])

    order_no = persist_franchise_order(plan, db)

    assert counts(engine) == (1, 2, 1)
    with Session(engine) as s:
        assert s.get(PurchaseOrder, order_no).total_amount == plan.total_amount
        rows = {d.prod_code: d for d in s.scalars(select(PurchaseOrderDetail))}
        assert set(rows) == {"A001", "B001"}
        for line in plan.details:
            row = rows[line.prod_code]
            assert row.purchase_order_no == order_no
            assert (row.qty, row.unit_price, row.net_price, row.vat, row.total_amount) == (
                line.qty, line.unit_price, line.net_price, line.vat, line.total_amount,
            )
        audit = s.scalars(select(AuditLog)).one()
        assert audit.purchase_order_no == order_no
        assert (audit.detail_count, audit.total_amount) == (2, plan.total_amount)
    assert product_rows(engine) == [("A001", 1000, True), ("B001", 200, True)]


def test_later_detail_insert_failure_leaves_no_records(engine, db):
    attempts = []
    completed = []
    with fail_on_insert(
        engine, "purchase_order_details", attempts, fail_if_param="B001", completed=completed
    ):
        with pytest.raises(InjectedFailure):
            persist_franchise_order(make_plan([("A001", 5), ("B001", 2)]), db)

    assert counts(engine) == (0, 0, 0)
    assert product_rows(engine) == [("A001", 1000, True), ("B001", 200, True)]
    # 앞선 상세(A001)의 INSERT가 별도 실행으로 먼저 전달됐고, 뒤쪽 상세(B001)에서 실패했다.
    # SQLAlchemy/SQLite 버전의 INSERT 묶음 방식에 의존하는 관찰이다.
    assert [params[1] for _, params, _ in attempts] == ["A001", "B001"]
    # A001 INSERT는 DB 커서 실행이 끝났고(after_cursor_execute), B001은 끝나지 않았다.
    assert [params[1] for params in completed] == ["A001"]


def test_session_with_open_transaction_is_rejected(engine, db):
    # 조회만 해도 Session이 트랜잭션을 자동 시작한다(autobegin).
    db.scalar(select(func.count()).select_from(Product))
    assert db.in_transaction()

    with pytest.raises(InvalidRequestError):
        persist_franchise_order(make_plan(), db)

    assert counts(engine) == (0, 0, 0)


def test_audit_insert_failure_leaves_no_records(engine, db):
    attempts = []
    with fail_on_insert(engine, "audit_logs", attempts):
        with pytest.raises(InjectedFailure):
            persist_franchise_order(make_plan([("A001", 5), ("B001", 2)]), db)

    assert counts(engine) == (0, 0, 0)
    assert product_rows(engine) == [("A001", 1000, True), ("B001", 200, True)]
    assert len(attempts) == 1


def test_listener_is_removed_after_failure(engine):
    with pytest.raises(RuntimeError):
        with fail_on_insert(engine, "audit_logs", []):
            raise RuntimeError("테스트 본문 실패 시뮬레이션")
    with Session(engine) as s, s.begin():
        s.add(PurchaseOrder(corp_id="c", partner_id="p", dept_code="d", emp_code="e",
                            delivery_code=1, is_vat="1", order_status="10", total_amount=0))
        s.add(AuditLog(purchase_order_no=1, action="INSERT", detail_count=0, total_amount=0))
    assert counts(engine) == (1, 0, 1)
