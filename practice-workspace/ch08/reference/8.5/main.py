# 파일 경로: project/main.py
from fastapi import FastAPI

from routers.franchise_order import router as franchise_order_router

app = FastAPI()
app.include_router(franchise_order_router)
