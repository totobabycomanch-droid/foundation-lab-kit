from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .lab_auth import LabSessions, SessionInput, current_user
from .store import LabStore
from . import approval_rules, defect_approval

ROOT = Path(__file__).resolve().parents[1]
SpaceName = Literal["main", "defect"]


@dataclass
class Workspace:
    store: LabStore
    sessions: LabSessions
    cookie_name: str


def create_app(data_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="Chapter 4 발주 승인 실습")
    data_dir = data_dir or ROOT / ".lab"
    app.state.spaces = {
        name: Workspace(LabStore(data_dir / f"{name}.sqlite3"), LabSessions(), f"ch04_{name}")
        for name in ("main", "defect")
    }

    @app.middleware("http")
    async def private_response(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.post("/api/{space}/session")
    def session(space: SpaceName, data: SessionInput, request: Request, response: Response):
        workspace = app.state.spaces[space]
        with workspace.store.operation():
            token, user = workspace.sessions.open(data.user_id, request.cookies.get(workspace.cookie_name))
            response.set_cookie(workspace.cookie_name, token, httponly=True,
                                samesite="strict", path=f"/api/{space}")
            return user

    @app.get("/api/{space}/me")
    def me(space: SpaceName, request: Request):
        with app.state.spaces[space].store.operation():
            return asdict(current_user(request))

    @app.get("/api/{space}/orders")
    def orders(space: SpaceName, request: Request):
        workspace = app.state.spaces[space]
        with workspace.store.operation():
            return workspace.store.list_orders(current_user(request).corp_id)

    @app.get("/api/{space}/orders/{order_id}")
    def detail(space: SpaceName, order_id: int, request: Request):
        workspace = app.state.spaces[space]
        with workspace.store.operation():
            order = workspace.store.find_order(order_id, current_user(request).corp_id)
            if order is None:
                raise HTTPException(404, "발주를 찾을 수 없습니다.")
            return order

    @app.post("/api/{space}/orders/{order_id}/approve")
    def approve(space: SpaceName, order_id: int, request: Request):
        workspace = app.state.spaces[space]
        with workspace.store.operation():
            user = current_user(request)
            if space == "defect":
                order = defect_approval.approve_order(workspace.store, order_id, user)
            else:
                order = workspace.store.approve_order(order_id, user, approval_rules.check_permission)
            if order is None:
                raise HTTPException(404, "발주를 찾을 수 없습니다.")
            return order

    @app.post("/api/{space}/reset")
    def reset(space: SpaceName, response: Response):
        workspace = app.state.spaces[space]
        if not workspace.store.reset(workspace.sessions.clear):
            raise HTTPException(409, "요청이 끝난 뒤 초기화하세요.")
        response.delete_cookie(workspace.cookie_name, path=f"/api/{space}")
        return {"status": "reset"}

    @app.get("/")
    def index():
        return FileResponse(ROOT / "frontend" / "index.html")

    @app.get("/vendor/vue.js")
    def vue():
        path = ROOT / "node_modules" / "vue" / "dist" / "vue.esm-browser.prod.js"
        if not path.is_file():
            raise HTTPException(503, "start_lab.ps1로 Vue를 설치한 뒤 실행하세요.")
        return FileResponse(path, media_type="text/javascript")

    app.mount("/frontend", StaticFiles(directory=ROOT / "frontend"), name="frontend")
    return app


app = create_app()
