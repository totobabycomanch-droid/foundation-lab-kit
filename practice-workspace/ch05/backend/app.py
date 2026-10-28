from pathlib import Path
from uuid import uuid4
from typing import Literal, Annotated
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from .store import LabStore
from . import movement_rules, movement_write
from .relationship_store import RelationshipStore
from . import relationship_write, relationship_read

ROOT = Path(__file__).resolve().parents[1]
ProductCode = Literal['A001', 'B001']


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')
    product_code: ProductCode
    direction: Literal['IN', 'OUT']
    quantity: Annotated[StrictInt, Field(gt=0, le=1000000)]


class ProductInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    code: Annotated[str, Field(strict=True, pattern=r'^[A-Z][A-Z0-9]{0,19}$')]


class PrepareInput(ProductInput):
    name: Annotated[str, Field(strict=True, min_length=1, max_length=60)]
    quantity: Annotated[StrictInt, Field(gt=0, le=1000000)]


def create_app(data_path=None):
    app = FastAPI(title='Chapter 5 입출고와 SQL 추적')
    app.state.store = LabStore(Path(data_path) if data_path else ROOT/'.lab/stock.sqlite3')
    app.state.relationships = RelationshipStore(app.state.store.path.with_name('relationships.sqlite3'))

    @app.middleware('http')
    async def no_cache(request: Request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, error):
        return JSONResponse(status_code=422, content={
            'request_id': str(uuid4()), 'status_code': 422, 'outcome': '미실행',
            'detail': ('상품코드·상품명·거래 수량을 확인하세요. 코드는 영문 대문자로 시작하는 영문 대문자·숫자 1~20자, 이름은 1~60자, 수량은 1~1,000,000의 정수입니다.' if request.url.path.startswith('/api/relationships') else '품목·입출고 구분과 수량을 확인하세요. 수량은 1~1,000,000의 정수입니다.'),
            'trace': [], 'snapshot': None})

    def response(code, trace, status=200, detail='DB에서 다시 조회했습니다.', outcome='조회', snapshot=None):
        return JSONResponse(status_code=status, content={
            'request_id': str(uuid4()), 'status_code': status, 'product_code': code,
            'detail': detail, 'outcome': outcome, 'trace': trace, 'snapshot': snapshot})

    @app.get('/api/state')
    def state(product_code: ProductCode = 'A001'):
        trace = []
        snapshot = app.state.store.observe(product_code, trace)
        return response(product_code, trace, snapshot=snapshot)

    @app.post('/api/movements')
    def move(data: Input):
        trace = []
        status, detail, outcome, snapshot = app.state.store.move(
            data.product_code, data.direction, data.quantity,
            movement_write.apply_movement, movement_rules.decide_movement, trace)
        return response(data.product_code, trace, status, detail, outcome, snapshot)

    @app.post('/api/reset')
    def reset(product_code: ProductCode = 'A001'):
        trace = []
        snapshot = app.state.store.reset(product_code, trace)
        return response(product_code, trace, detail='두 품목의 현재고와 이력을 초기화했습니다.', outcome='확정', snapshot=snapshot)

    @app.get('/')
    def index():
        return FileResponse(ROOT/'frontend/index.html')

    def relation_response(action, data=None):
        trace = []
        status, detail, outcome, snapshot = app.state.relationships.run(
            action, data or {}, relationship_write.change_product, relationship_read.read_relationships, trace)
        return response((data or {}).get('code'), trace, status, detail, outcome, snapshot)

    @app.get('/relationships')
    def relationships_page():
        return FileResponse(ROOT/'frontend/relationships.html')

    @app.get('/api/relationships/state')
    def relationship_state():
        return relation_response('state')

    @app.post('/api/relationships/prepare')
    def relationship_prepare(data: PrepareInput):
        return relation_response('prepare', data.model_dump())

    @app.post('/api/relationships/delete')
    def relationship_delete(data: ProductInput):
        return relation_response('delete', data.model_dump())

    @app.post('/api/relationships/discontinue')
    def relationship_discontinue(data: ProductInput):
        return relation_response('discontinue', data.model_dump())

    @app.post('/api/relationships/reset')
    def relationship_reset():
        return relation_response('reset')

    app.mount('/frontend', StaticFiles(directory=ROOT/'frontend'), name='frontend')
    return app


app = create_app()
