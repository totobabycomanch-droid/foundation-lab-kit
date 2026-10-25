# api/main.py
import os
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()  # 실행 터미널의 기존 DATABASE_URL을 해제한 뒤 백엔드 .env 로드

# 1. 데이터베이스 연결 설정
engine = create_engine(os.environ["DATABASE_URL"], hide_parameters=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 2. Pydantic 요청 스키마 정의
class ApproveOrderRequest(BaseModel):
    """주문 승인 요청 바디 스키마"""
    order_id: UUID
    product_id: str
    qty: int = Field(ge=1)

# 3. FastAPI 인스턴스 생성 및 CORS 설정
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue 개발 서버 기본 포트
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. 주문 승인 API 엔드포인트 정의
@app.post("/orders/approve")
def approve_order_api(
    request: ApproveOrderRequest, 
    db=Depends(get_db)
):
    try:
        # 아키텍처 원칙: 핵심 트랜잭션 및 데이터 정합성 로직은 DB 함수에 위임 (Thin Layer API)
        # SQLAlchemy 2.0 호환을 위해 text()를 사용해 쿼리를 감싸줍니다.
        db.execute(
            text("SELECT approve_order(:id, :pid, :q)"),
            {
                "id": request.order_id,
                "pid": request.product_id,
                "q": request.qty
            }
        )
        db.commit()  # 트랜잭션 확정
        return {"status": "success"}
    except Exception as e:
        db.rollback()  # 오류 발생 시 롤백
        raise HTTPException(status_code=400, detail=str(e))
