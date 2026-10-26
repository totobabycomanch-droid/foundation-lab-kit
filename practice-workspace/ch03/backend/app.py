import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .order_write import router
from .company_read import router as company_router
from .lab_auth import LabSessions, router as lab_auth_router
from .store import LabStore

ROOT = Path(__file__).resolve().parents[1]


def create_app(db_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="Chapter 3 발주 실습")
    app.state.store = LabStore(db_path or ROOT / ".lab" / "orders.sqlite3")
    app.state.lab_sessions = LabSessions()

    @app.middleware("http")
    async def private_lab_response(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/lab/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.middleware("http")
    async def observe_save(request, call_next):
        if request.method != "POST" or request.url.path != "/api/orders":
            return await call_next(request)
        app.state.store.begin_request()
        try:
            # 화면의 저장 중 상태를 일정하게 관찰하기 위한 실습 장치입니다.
            await asyncio.sleep(1.2)
            return await call_next(request)
        finally:
            app.state.store.end_request()

    app.include_router(router)
    app.include_router(lab_auth_router)
    app.include_router(company_router)

    @app.get("/api/orders")
    def list_orders():
        return app.state.store.list_orders()

    @app.get("/api/observations")
    def observations():
        return app.state.store.observations()

    @app.post("/api/reset")
    def reset():
        if not app.state.store.reset():
            raise HTTPException(status_code=409, detail="저장 요청이 끝난 뒤 초기화하세요.")
        return {"status": "reset"}

    @app.get("/")
    def index():
        return FileResponse(ROOT / "frontend" / "index.html")

    @app.get("/vendor/vue.js")
    def vue_module():
        return FileResponse(ROOT / "node_modules" / "vue" / "dist" / "vue.esm-browser.prod.js", media_type="text/javascript")

    app.mount("/frontend", StaticFiles(directory=ROOT / "frontend"), name="frontend")
    return app


app = create_app()
