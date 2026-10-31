from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from db import get_connection


app = FastAPI(title="Chapter 10 ERP Mini")


@app.get("/health")
def health():
    return {"status": "ok"}


class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)


class OrderRequest(BaseModel):
    corp_id: str
    items: List[OrderItem] = Field(min_length=1)


@app.post('/orders')
def create_order(req: OrderRequest):
    # AI와 주문 저장·단가 결정·재고 확인·확정/취소를 구현합니다.
    # lab_app은 이 연결 함수를 관찰하지만 업무 저장을 대신하지 않습니다.
    raise HTTPException(501, '주문 저장 미구현: AGENTS.md와 README.md를 읽고 AI와 완성하세요.')

