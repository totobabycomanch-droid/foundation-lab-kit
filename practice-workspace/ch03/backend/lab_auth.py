"""Prepared local test sessions; user selection is not production authentication."""
from dataclasses import asdict, dataclass
from secrets import token_urlsafe
from threading import Lock
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict

COOKIE_NAME = "ch03_lab_session"


@dataclass(frozen=True)
class LabUser:
    user_id: str
    corp_id: str
    corp_name: str


USERS = {
    "user_a": LabUser("user_a", "A", "A회사"),
    "user_b": LabUser("user_b", "B", "B회사"),
}


class LabSessions:
    def __init__(self):
        self._users_by_session: dict[str, LabUser] = {}
        self._lock = Lock()

    def open(self, user_id: str, previous: str | None) -> tuple[str, LabUser]:
        with self._lock:
            if previous:
                self._users_by_session.pop(previous, None)
            session = token_urlsafe(32)
            user = USERS[user_id]
            self._users_by_session[session] = user
            return session, user

    def resolve(self, session: str | None) -> LabUser | None:
        with self._lock:
            return self._users_by_session.get(session)


def current_lab_user(request: Request) -> LabUser:
    user = request.app.state.lab_sessions.resolve(request.cookies.get(COOKIE_NAME))
    if user is None:
        raise HTTPException(status_code=401, detail="테스트 사용자를 선택하세요.")
    return user


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: Literal["user_a", "user_b"]


router = APIRouter(prefix="/api/lab")


@router.post("/login")
def login(data: LoginInput, request: Request, response: Response):
    session, user = request.app.state.lab_sessions.open(data.user_id, request.cookies.get(COOKIE_NAME))
    response.set_cookie(COOKIE_NAME, session, httponly=True, samesite="strict", path="/api/lab")
    response.headers["Cache-Control"] = "no-store"
    return asdict(user)


@router.get("/me")
def me(request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return asdict(current_lab_user(request))
