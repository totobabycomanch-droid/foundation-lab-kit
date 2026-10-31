"""Provided local UI, observation and failure injection around learner server.py."""
import asyncio
import json
from pathlib import Path
from uuid import uuid4
from typing import Literal

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import server
import lab_store as store

app = server.app
# Only connection observation is provided; learner code owns commit/rollback.
server.get_connection = store.ObservedConnection
lock = asyncio.Lock()
FRONTEND = Path(__file__).with_name('frontend')
app.mount('/assets', StaticFiles(directory=FRONTEND), name='assets')


@app.middleware('http')
async def observe(request: Request, call_next):
    if request.method != 'POST' or request.url.path != '/orders':
        return await call_next(request)
    async with lock:
        trace = []
        token = store.TRACE.set(trace)
        failure = store.FAIL_SECOND.set(request.headers.get('X-Lab-Fail-Second') == 'yes')
        request_id = str(uuid4())
        try:
            try:
                before = await asyncio.to_thread(store.snapshot)
            except Exception:
                return JSONResponse(status_code=503, content=dict(detail='전용 DB 연결·표식·스키마·초기 데이터를 확인하세요.'))
            try:
                response = await call_next(request)
                raw = b''.join([chunk async for chunk in response.body_iterator])
                body = json.loads(raw)
                status = response.status_code
            except Exception:
                body, status = dict(detail='주문 처리 오류. 코드와 실행 근거를 확인하세요.'), 500
            # Never expose arbitrary learner exception text or submitted data.
            if status >= 500 and status != 501:
                body = dict(detail='주문 저장 실패. 아래 DB 오류와 저장 전후 값을 확인하세요.')
            try:
                after = await asyncio.to_thread(store.snapshot)
                observed = '확인됨'
            except Exception:
                after, observed = None, '미확인: 저장 후 DB 조회 실패'
            body['observation'] = dict(request_id=request_id, failure_requested=store.FAIL_SECOND.get(),
                before=before, after=after, trace=trace, observed=observed)
            return JSONResponse(status_code=status, content=body)
        finally:
            store.TRACE.reset(token)
            store.FAIL_SECOND.reset(failure)


@app.get('/', include_in_schema=False)
def index():
    return FileResponse(FRONTEND / 'index.html')


@app.get('/lab/snapshot')
async def read_snapshot():
    async with lock:
        try:
            return await asyncio.to_thread(store.snapshot)
        except Exception:
            raise HTTPException(503, '전용 DB 연결·표식·스키마·초기 데이터를 확인하세요.') from None


class PriceChange(BaseModel):
    price: Literal[5000, 6000]


@app.post('/lab/price')
async def price_change(req: PriceChange):
    async with lock:
        try:
            await asyncio.to_thread(store.change_price, req.price)
        except Exception:
            raise HTTPException(503, '가격 변경 미확인. DB 준비 상태를 확인하고 현재 값을 다시 조회하세요.') from None
        try:
            after = await asyncio.to_thread(store.snapshot)
        except Exception:
            raise HTTPException(503, '가격 변경 후 조회 미확인. 현재 값을 다시 조회하세요.') from None
        return dict(action='가격 변경' if req.price == 6000 else '가격 원복', after=after)
