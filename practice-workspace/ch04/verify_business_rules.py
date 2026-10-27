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
        raise RuntimeError("Unexpected HTTP redirect from the local test server")


class Client:
    def __init__(self, port):
        self.base = f"http://127.0.0.1:{port}"
        self.opener = build_opener(
            ProxyHandler({}), NoRedirect(), HTTPCookieProcessor(CookieJar()),
        )

    def request(self, space, path, method="GET", body=None):
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
        status, body = self.request(space, "/session", "POST", {"user_id": user})
        require(status == 200 and body.get("user_id") == user, "test-user login failed")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def snapshot(workspace):
    result = {}
    for space in ("main", "defect"):
        path = (workspace / ".lab" / f"{space}.sqlite3").resolve()
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
            db.row_factory = sqlite3.Row
            result[space] = [dict(row) for row in db.execute("SELECT * FROM orders ORDER BY id")]
    return result


def check_database(actual, expected, reason):
    for space in ("main", "defect"):
        if actual[space] != expected[space]:
            compact = lambda rows: [(row["id"], row["status"], row["approval_count"]) for row in rows]
            raise AssertionError(
                f"{reason}: {space} expected(id,status,count)={compact(expected[space])} "
                f"actual={compact(actual[space])}; full rows compared"
            )


def check_case(workspace, port, space, case):
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
