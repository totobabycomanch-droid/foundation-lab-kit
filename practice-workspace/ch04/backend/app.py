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
    """두 실습 공간의 DB·세션과 API를 구성해 FastAPI 앱을 반환한다.

    data_dir를 생략하면 현재 Chapter의 .lab에 DB를 만든다.
    본 실습과 결함 실습은 저장소·세션·쿠키 이름을 각각 따로 사용한다.
    """
    app = FastAPI(title="Chapter 4 발주 승인 실습")
    data_dir = data_dir or ROOT / ".lab"
    app.state.spaces = {
        name: Workspace(LabStore(data_dir / f"{name}.sqlite3"), LabSessions(), f"ch04_{name}")
        for name in ("main", "defect")
    }

    @app.middleware("http")
    async def private_response(request: Request, call_next):
        """API 응답을 캐시에 남기지 않아 재조회 시 오래된 관찰값을 쓰지 않게 한다."""
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.post("/api/{space}/session")
    def session(space: SpaceName, data: SessionInput, request: Request, response: Response):
        """선택한 사용자의 세션을 열고 토큰을 해당 공간의 쿠키에 설정한다.

        본문에는 사용자 ID만 받으며, 회사·역할은 서버의 고정 정보에서 얻는다.
        응답 본문에는 화면에 표시할 사용자 정보를 반환한다.
        """
        workspace = app.state.spaces[space]
        with workspace.store.operation():
            token, user = workspace.sessions.open(data.user_id, request.cookies.get(workspace.cookie_name))
            response.set_cookie(workspace.cookie_name, token, httponly=True,
                                samesite="strict", path=f"/api/{space}")
            return user

    @app.get("/api/{space}/me")
    def me(space: SpaceName, request: Request):
        """현재 공간의 서버 세션에서 확인한 사용자 정보를 화면에 반환한다."""
        with app.state.spaces[space].store.operation():
            return asdict(current_user(request))

    @app.get("/api/{space}/orders")
    def orders(space: SpaceName, request: Request):
        """서버가 확인한 사용자 회사로 발주 목록의 조회 범위를 제한한다."""
        workspace = app.state.spaces[space]
        with workspace.store.operation():
            return workspace.store.list_orders(current_user(request).corp_id)

    @app.get("/api/{space}/orders/{order_id}")
    def detail(space: SpaceName, order_id: int, request: Request):
        """자기 회사의 발주 상세를 반환하고, 조회 대상이 없으면 404로 응답한다.

        다른 회사 발주와 없는 번호는 같은 메시지로 처리한다.
        """
        workspace = app.state.spaces[space]
        with workspace.store.operation():
            order = workspace.store.find_order(order_id, current_user(request).corp_id)
            if order is None:
                raise HTTPException(404, "발주를 찾을 수 없습니다.")
            return order

    @app.post("/api/{space}/orders/{order_id}/approve")
    def approve(space: SpaceName, order_id: int, request: Request):
        """서버 사용자 정보를 얻어 현재 공간의 승인 흐름에 전달한다.

        본 실습은 store와 approval_rules를, 결함 실습은 defect_approval를
        사용한다. 대상이 없으면 404로 응답하고 성공하면 저장된 발주를 반환한다.
        업무 판단의 403·409 예외는 FastAPI가 거부 응답으로 변환한다.
        """
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
        """현재 공간의 데이터·세션을 초기화하고 브라우저 쿠키도 지운다.

        요청 처리 중이라 초기화하지 못하면 409로 응답한다. 코드는 되돌리지 않는다.
        """
        workspace = app.state.spaces[space]
        if not workspace.store.reset(workspace.sessions.clear):
            raise HTTPException(409, "요청이 끝난 뒤 초기화하세요.")
        response.delete_cookie(workspace.cookie_name, path=f"/api/{space}")
        return {"status": "reset"}

    @app.get("/")
    def index():
        """실습 화면의 HTML 파일을 제공한다."""
        return FileResponse(ROOT / "frontend" / "index.html")

    @app.get("/vendor/vue.js")
    def vue():
        """로컬에 설치된 Vue를 제공하고, 설치 파일이 없으면 503으로 안내한다."""
        path = ROOT / "node_modules" / "vue" / "dist" / "vue.esm-browser.prod.js"
        if not path.is_file():
            raise HTTPException(503, "start_lab.ps1로 Vue를 설치한 뒤 실행하세요.")
        return FileResponse(path, media_type="text/javascript")

    app.mount("/frontend", StaticFiles(directory=ROOT / "frontend"), name="frontend")
    return app


app = create_app()
