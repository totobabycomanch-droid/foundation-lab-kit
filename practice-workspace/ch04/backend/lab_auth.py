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
        """이 실습 공간의 접속 정보를 서버 메모리에 보관할 준비를 한다."""
        self._sessions: dict[str, LabUser] = {}
        self._lock = Lock()

    def open(self, user_id: str, previous: str | None) -> tuple[str, dict]:
        """선택한 실습 사용자로 접속하고 새 세션 토큰과 사용자 정보를 반환한다.

        회사·역할은 요청값 대신 USERS의 고정 정보에서 얻는다.
        이전 토큰은 폐기하며, 반환한 새 토큰은 API에서 쿠키로 설정한다.
        """
        with self._lock:
            self._sessions.pop(previous, None)
            token = token_urlsafe(32)
            user = USERS[user_id]
            self._sessions[token] = user
            return token, asdict(user)

    def resolve(self, token: str | None) -> LabUser:
        """쿠키의 토큰으로 서버가 기억한 사용자를 찾고, 없으면 401로 거부한다."""
        with self._lock:
            user = self._sessions.get(token)
        if user is None:
            raise HTTPException(401, "실습 사용자를 선택해 주세요.")
        return user

    def clear(self):
        """이 공간의 모든 접속 정보를 지워 기존 토큰을 사용할 수 없게 한다."""
        with self._lock:
            self._sessions.clear()


def current_user(request: Request) -> LabUser:
    """현재 실습 공간의 쿠키와 서버 세션으로 사용자·회사·역할을 확인한다.

    요청 본문이나 쿼리에 적힌 회사·역할을 사용자 정보로 사용하지 않는다.
    유효한 접속 정보가 없으면 resolve가 401 예외를 발생시킨다.
    """
    space = request.app.state.spaces[request.path_params["space"]]
    return space.sessions.resolve(request.cookies.get(space.cookie_name))
