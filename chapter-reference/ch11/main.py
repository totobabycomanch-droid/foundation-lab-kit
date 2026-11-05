"""전용 실습 DB의 주문 승인·현재 상태 조회 API 참조 구현."""
from functools import lru_cache
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from lab_db import CASES, settings

BUSINESS_ERRORS = {
    'P1101': '수량은 1 이상이어야 합니다.',
    'P1102': '주문 정보가 존재하지 않습니다.',
    'P1103': '요청 상품 또는 수량이 저장된 주문과 다릅니다.',
    'P1104': '이미 승인된 주문입니다.',
    'P1105': '상품 정보가 존재하지 않습니다.',
    'P1106': '재고가 부족합니다.',
}


class ApproveOrderRequest(BaseModel):
    order_id: UUID
    product_id: str
    qty: int = Field(ge=1, le=2147483647, strict=True)


class ChangeQuantityRequest(BaseModel):
    order_id: UUID
    qty: int = Field(ge=1, le=2147483647, strict=True)


@lru_cache(maxsize=1)
def local_session_factory():
    # 연결값은 도구가 내부 사용합니다. 상속된 다른 DB 환경변수는 사용하지 않습니다.
    config = settings()
    url = URL.create('postgresql+psycopg2', username=config['user'], password=config['password'],
                     host=config['host'], port=config['port'], database=config['dbname'])
    engine = create_engine(url, hide_parameters=True, pool_pre_ping=True,
                           connect_args={'sslmode': config['sslmode'], 'connect_timeout': 10,
                                         'options': '-c statement_timeout=15000 -c lock_timeout=5000'})
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def rollback_quietly(session):
    try:
        session.rollback()
    except SQLAlchemyError:
        pass


def check_lab(session):
    identity = session.execute(text('SELECT current_database(), session_user')).one()
    if identity[0] != 'postgres' or not (identity[1] == 'postgres' or identity[1].startswith('postgres.')):
        raise HTTPException(status_code=503, detail='전용 실습 DB 연결을 확인해 주세요.')
    marker = session.execute(text("SELECT 1 FROM public.foundation_lab_marker WHERE lab_id='chapter11'")).first()
    if marker is None:
        raise HTTPException(status_code=503, detail='Chapter 11 전용 실습 DB 표식이 없습니다.')


def create_app(session_factory=None):
    app = FastAPI(title='Chapter 11 주문 승인')
    app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173'],
                       allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])

    def get_db():
        try:
            factory = session_factory if session_factory is not None else local_session_factory()
            session = factory()
        except Exception:
            raise HTTPException(status_code=503, detail='로컬 전용 DB 연결 설정을 확인해 주세요.') from None
        try:
            yield session
        finally:
            try:
                session.close()
            except SQLAlchemyError:
                pass

    @app.get('/orders')
    def list_orders(db=Depends(get_db)):
        try:
            check_lab(db)
            rows = db.execute(text(
                'SELECT o.order_id,o.order_name,o.product_id,s.product_name,o.quantity AS qty,'
                's.quantity AS current_stock,o.status FROM public.orders o '
                'JOIN public.stock s ON s.product_id=o.product_id '
                'WHERE o.order_id IN (:a,:b) ORDER BY o.order_id'),
                {'a': CASES['A'][0], 'b': CASES['B'][0]}).mappings().all()
            return {'items': [dict(row) for row in rows]}
        except SQLAlchemyError:
            rollback_quietly(db)
            raise HTTPException(status_code=503, detail='주문 상태를 읽지 못했습니다. 다시 조회해 주세요.') from None

    @app.post('/orders/quantity')
    def change_quantity(request: ChangeQuantityRequest, db=Depends(get_db)):
        committing = False
        try:
            check_lab(db)
            db.execute(text('SELECT public.change_order_quantity(:id,:qty)'),
                       {'id': request.order_id, 'qty': request.qty})
            committing = True
            db.commit()
            return {'status': 'success'}
        except SQLAlchemyError as error:
            rollback_quietly(db)
            code = getattr(getattr(error, 'orig', None), 'pgcode', None)
            if not committing and code in BUSINESS_ERRORS:
                raise HTTPException(status_code=400, detail=BUSINESS_ERRORS[code]) from None
            raise HTTPException(status_code=503, detail='수량 저장 결과를 확인하지 못했습니다. 현재 상태를 다시 조회해 주세요.') from None

    @app.post('/orders/approve')
    def approve_order(request: ApproveOrderRequest, db=Depends(get_db)):
        committing = False
        try:
            check_lab(db)
            db.execute(text('SELECT public.approve_order(:id,:pid,:qty)'),
                       {'id': request.order_id, 'pid': request.product_id, 'qty': request.qty})
            committing = True
            db.commit()
            return {'status': 'success'}
        except SQLAlchemyError as error:
            rollback_quietly(db)
            code = getattr(getattr(error, 'orig', None), 'pgcode', None)
            if not committing and code in BUSINESS_ERRORS:
                raise HTTPException(status_code=400, detail=BUSINESS_ERRORS[code]) from None
            # 커밋 중 장애는 저장 취소를 단정할 수 없습니다.
            raise HTTPException(status_code=503, detail='처리 결과를 확인하지 못했습니다. 현재 상태를 다시 조회해 주세요.') from None

    return app


app = create_app()
