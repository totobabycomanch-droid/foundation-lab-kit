"""Optional HTTP checks for completed Chapter 4 code, using disposable copies only."""
from contextlib import closing, contextmanager
from dataclasses import dataclass
from http.client import HTTPException as HTTPTransportError
from http.cookiejar import CookieJar
import importlib.util
import json
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import (
    HTTPRedirectHandler, HTTPCookieProcessor, ProxyHandler, Request, build_opener,
)


ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Case:
    name: str
    user: str | None
    order_id: int
    status: int
    forged: str = ""


CASES = (
    Case("no-session", None, 1001, 401),
    Case("manager-pending", "a_manager", 1001, 200),
    Case("manager-approved", "a_manager", 1002, 409),
    Case("reader-pending", "a_reader", 1001, 403),
    Case("reader-approved", "a_reader", 1002, 403),
    Case("manager-other-company", "a_manager", 2001, 404),
    Case("reader-other-company", "a_reader", 2001, 404),
    Case("manager-missing", "a_manager", 9999, 404),
    Case("reader-missing", "a_reader", 9999, 404),
    Case("other-company-owner", "b_manager", 2001, 200),
    Case("forged-query-company", "a_manager", 2001, 404, "query"),
    Case("forged-body-company", "a_manager", 2001, 404, "body"),
)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        """예상하지 않은 HTTP 리다이렉트를 따라가지 않고 검사 오류로 알린다."""
        raise RuntimeError("Unexpected HTTP redirect from the local test server")


class Client:
    def __init__(self, port):
        """임시 로컬 서버로 요청할 클라이언트와 독립된 쿠키 저장소를 준비한다."""
        self.base = f"http://127.0.0.1:{port}"
        self.opener = build_opener(
            ProxyHandler({}), NoRedirect(), HTTPCookieProcessor(CookieJar()),
        )

    def request(self, space, path, method="GET", body=None):
        """지정한 공간의 API를 호출하고 실제 HTTP 상태 코드와 JSON 객체를 반환한다.

        403·404 같은 오류 응답도 검사 대상이므로 HTTPError에서 응답을 읽는다.
        본문이 유효한 JSON 객체가 아니면 AssertionError로 검사 실패를 알린다.
        """
        payload = None if body is None else json.dumps(body).encode("utf-8")
        req = Request(self.base + f"/api/{space}" + path, data=payload, method=method)
        if payload is not None:
            req.add_header("Content-Type", "application/json")
        try:
            response = self.opener.open(req, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            try:
                result = json.loads(response.read().decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise AssertionError(f"HTTP {response.code} {method} {path}: response is not valid JSON") from error
            require(isinstance(result, dict),
                    f"HTTP {response.code} {method} {path}: expected JSON object, got {type(result).__name__}")
            return response.code, result

    def login(self, space, user):
        """임시 서버에서 실습 사용자를 선택하고 응답의 사용자 ID까지 확인한다."""
        status, body = self.request(space, "/session", "POST", {"user_id": user})
        require(status == 200 and body.get("user_id") == user, "test-user login failed")


def require(condition, message):
    """검사 조건이 거짓이면 원인을 담은 AssertionError를 발생시킨다."""
    if not condition:
        raise AssertionError(message)


def snapshot(workspace):
    """두 임시 DB의 모든 발주를 읽기 전용으로 조회해 비교용 사전으로 반환한다.

    응답 메시지만 믿지 않고 요청 전후의 실제 저장값을 비교하는 데 사용한다.
    """
    result = {}
    for space in ("main", "defect"):
        path = (workspace / ".lab" / f"{space}.sqlite3").resolve()
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
            db.row_factory = sqlite3.Row
            result[space] = [dict(row) for row in db.execute("SELECT * FROM orders ORDER BY id")]
    return result


def check_database(actual, expected, reason):
    """두 공간의 전체 발주 행을 비교하고 예상 밖의 변경이 있으면 실패시킨다.

    화면용 요약에는 번호·상태·횟수를 표시하지만 실제 비교는 모든 컬럼을 대상으로 한다.
    """
    for space in ("main", "defect"):
        if actual[space] != expected[space]:
            compact = lambda rows: [(row["id"], row["status"], row["approval_count"]) for row in rows]
            raise AssertionError(
                f"{reason}: {space} expected(id,status,count)={compact(expected[space])} "
                f"actual={compact(actual[space])}; full rows compared"
            )


def check_case(workspace, port, space, case):
    """한 승인 사례의 응답과 DB 변경 여부를 확인하고 소유자 API로 재조회한다.

    각 사례는 두 임시 공간을 초기화한 뒤 실행한다. 성공 시 대상 발주만
    한 번 갱신돼야 하고, 거부 시 두 DB의 모든 발주가 그대로여야 한다.
    case의 기대 응답은 완성한 규칙의 기준이며, 시작본은 일부 사례에 실패한다.
    """
    # Reset only the disposable databases. Each row starts with the same seeds.
    client = Client(port)
    for name in ("main", "defect"):
        status, _ = client.request(name, "/reset", "POST")
        require(status == 200, f"temporary {name} reset failed")
    before = snapshot(workspace)
    actor = Client(port)
    if case.user:
        actor.login(space, case.user)
    query = "?corp_id=B" if case.forged == "query" else ""
    payload = {"corp_id": "B"} if case.forged == "body" else None
    status, body = actor.request(space, f"/orders/{case.order_id}/approve{query}", "POST", payload)
    after = snapshot(workspace)
    require(status == case.status, f"expected HTTP {case.status}, got {status}")
    if status == 200:
        expected = json.loads(json.dumps(before))
        order = next(row for row in expected[space] if row["id"] == case.order_id)
        order["status"] = "APPROVED"
        order["approval_count"] += 1
        check_database(after, expected, "unexpected database change after approval")
        require(body == order, "success response differs from stored order")
    else:
        check_database(after, before, "rejected request changed a database")
        if status == 403:
            require(isinstance(body.get("detail"), str) and bool(body["detail"].strip()), "missing denial reason")
            require(set(body) == {"detail"}, "denial response includes unexpected fields")
        else:
            detail = {
                401: "실습 사용자를 선택해 주세요.",
                404: "발주를 찾을 수 없습니다.",
                409: "승인 대기 발주만 승인할 수 있습니다.",
            }[status]
            require(body == {"detail": detail}, "error message differs or exposes order data")
    # Confirm the observable value through the owner's API as well as the database.
    stored = next((row for row in after[space] if row["id"] == case.order_id), None)
    if stored:
        owner = Client(port)
        owner.login(space, "a_manager" if stored["corp_id"] == "A" else "b_manager")
        read_status, observed = owner.request(space, f"/orders/{case.order_id}")
        require(read_status == 200 and observed == stored, "owner re-query differs from stored order")


def worker(workspace):
    """별도 프로세스에서 복사된 코드로 임시 서버를 실행한다.

    OS가 고른 빈 로컬 포트를 port.json에 기록해 검사 프로세스에 알린다.
    앱을 가져올 때 만드는 DB도 임시 workspace 안에만 생성된다.
    """
    # The child imports only the copied backend. app.py's import-time DB creation
    # therefore also stays under the temporary directory.
    sys.path.insert(0, str(workspace))
    import uvicorn
    from backend.app import app

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(128)
        port = listener.getsockname()[1]
        (workspace / "port.json").write_text(json.dumps(port), encoding="utf-8")
        server = uvicorn.Server(uvicorn.Config(app, log_level="error", access_log=False))
        server.run(sockets=[listener])


@contextmanager
def isolated_server():
    """코드를 임시 폴더로 복사해 서버를 띄우고 검사 후 프로세스와 폴더를 정리한다.

    준비된 임시 폴더와 포트를 with 블록에 제공한다. 기존 실습 DB와 실행 중인
    서버는 사용하지 않으며, 서버 준비에 실패하면 예외로 미실행 원인을 알린다.
    """
    with tempfile.TemporaryDirectory(prefix="ch04-business-") as directory:
        workspace = Path(directory)
        for name in ("backend", "frontend"):
            shutil.copytree(ROOT / name, workspace / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        with tempfile.TemporaryFile() as logs:
            process = subprocess.Popen(
                [sys.executable, "-B", str(Path(__file__).resolve()), "--worker", str(workspace)],
                cwd=workspace, stdin=subprocess.DEVNULL, stdout=logs, stderr=logs,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            try:
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        logs.seek(0)
                        lines = logs.read().decode("utf-8", errors="replace").strip().splitlines()
                        reason = lines[-1][:200] if lines else "check backend imports"
                        raise RuntimeError(f"temporary server exited before startup: {reason}")
                    port_file = workspace / "port.json"
                    if port_file.exists():
                        try:
                            port = json.loads(port_file.read_text(encoding="utf-8"))
                            status, _ = Client(port).request("main", "/me")
                            break  # Any HTTP reply means the server is ready for the checks.
                        except AssertionError:
                            break  # A malformed API reply is a case failure, not a startup failure.
                        except (OSError, ValueError, HTTPTransportError):
                            pass
                    time.sleep(0.05)
                else:
                    raise RuntimeError("temporary server startup timed out")
                yield workspace, port
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)


def main():
    """완성 기준의 API 24개 사례를 실행하고 Pass·Fail·Not Run을 구분한다.

    두 공간에서 각각 12개 사례를 실행한다. 반환값은 모두 통과 0, 기준 실패 1,
    미실행·환경 문제 2이며 실패가 있으면 1이 우선한다. 화면 버튼·동시 요청·
    저장 실패는 이 도구가 검증하지 않는다.
    """
    if any(importlib.util.find_spec(name) is None for name in ("fastapi", "uvicorn")):
        print("NOT RUN use .venv/Scripts/python.exe after start_lab.ps1 installs dependencies")
        print("RESULT Pass=0 Fail=0 Not Run=24 Total=24")
        return 2
    passed = failed = not_run = 0
    infrastructure_error = False
    print("Completed Chapter 4 only: 10 matrix rows + 2 forged-company cases per space.")
    print("Testing temporary copies; the original .lab and running server are not used.")
    try:
        with isolated_server() as (workspace, port):
            for space in ("main", "defect"):
                for case in CASES:
                    label = f"{space}/{case.name} user={case.user or 'none'} order={case.order_id} expected={case.status}"
                    try:
                        check_case(workspace, port, space, case)
                    except AssertionError as error:
                        failed += 1
                        print(f"FAIL {label}: {error}")
                    except (OSError, ValueError, RuntimeError, sqlite3.Error, HTTPTransportError) as error:
                        not_run += 1
                        action = "check temporary DB schema and backend imports" if isinstance(error, sqlite3.Error) else "check API execution and local dependencies"
                        print(f"NOT RUN {label}: {type(error).__name__}; {action}")
                    else:
                        passed += 1
                        print(f"PASS {label} actual={case.status} database+owner-query checked")
    except Exception as error:
        infrastructure_error = True
        not_run = 24 - passed - failed
        # Still report completed cases if setup, observation or cleanup fails unexpectedly.
        print(f"NOT RUN verification setup/observation/cleanup: {type(error).__name__}: {error}")
    print(f"RESULT Pass={passed} Fail={failed} Not Run={not_run} Total=24")
    print("UI buttons, concurrent requests and storage failures are not tested.")
    return 1 if failed else (2 if not_run or infrastructure_error else 0)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        worker(Path(sys.argv[2]).resolve())
    elif len(sys.argv) == 1:
        raise SystemExit(main())
    else:
        print("Usage: python verify_business_rules.py (after completing exercise 4)")
        raise SystemExit(2)
