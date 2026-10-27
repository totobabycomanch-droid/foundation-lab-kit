"""Prepared test users, not production authentication."""
from dataclasses import asdict, dataclass
from secrets import token_urlsafe
from threading import Lock
from typing import Literal

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict


@dataclass(frozen=True)
class LabUser:
    user_id: str
    corp_id: str
    role: str
    display_name: str


USERS = {
    "a_reader": LabUser("a_reader", "A", "READER", "A회사 조회 담당자"),
    "a_manager": LabUser("a_manager", "A", "MANAGER", "A회사 관리자"),
    "b_manager": LabUser("b_manager", "B", "MANAGER", "B회사 관리자"),
}


class SessionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: Literal["a_reader", "a_manager", "b_manager"]


class LabSessions:
    def __init__(self):
        self._sessions: dict[str, LabUser] = {}
        self._lock = Lock()

    def open(self, user_id: str, previous: str | None) -> tuple[str, dict]:
        with self._lock:
            self._sessions.pop(previous, None)
            token = token_urlsafe(32)
            user = USERS[user_id]
            self._sessions[token] = user
            return token, asdict(user)

    def resolve(self, token: str | None) -> LabUser:
        with self._lock:
            user = self._sessions.get(token)
        if user is None:
            raise HTTPException(401, "실습 사용자를 선택해 주세요.")
        return user

    def clear(self):
        with self._lock:
            self._sessions.clear()


def current_user(request: Request) -> LabUser:
    space = request.app.state.spaces[request.path_params["space"]]
    return space.sessions.resolve(request.cookies.get(space.cookie_name))
