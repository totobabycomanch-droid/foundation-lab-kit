"""Fixed SQLite data and reset boundary; one database per workspace."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from threading import Lock

SEEDS = (
    (1001, "A", "A회사 승인 대기 발주", 2, "PENDING", 0),
    (1002, "A", "A회사 승인 완료 발주", 3, "APPROVED", 1),
    (2001, "B", "B회사 승인 대기 발주", 4, "PENDING", 0),
)


class LabStore:
    def __init__(self, path: Path):
        """SQLite 파일과 발주 테이블을 준비하고, 없는 시작 데이터만 추가한다.

        서버를 다시 실행해도 기존 발주의 상태와 처리 횟수를 덮어쓰지 않는다.
        """
        self.path = path
        self._activity = Lock()
        self._active = 0
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY, corp_id TEXT NOT NULL,
                item_name TEXT NOT NULL, quantity INTEGER NOT NULL,
                status TEXT NOT NULL, approval_count INTEGER NOT NULL
            )""")
            # Initialization never overwrites changes made in an earlier server run.
            db.executemany("INSERT OR IGNORE INTO orders VALUES (?, ?, ?, ?, ?, ?)", SEEDS)

    @contextmanager
    def connect(self):
        """DB 연결을 제공하고 정상 종료하면 커밋, 예외가 나면 롤백한다.

        with 블록을 마칠 때 연결도 닫는다. 조회 행은 컬럼명으로 읽을 수 있다.
        """
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @contextmanager
    def operation(self):
        """진행 중인 요청 수를 관리해 요청 처리 도중의 초기화를 막는다.

        요청이 성공하든 예외로 끝나든 finally에서 진행 수를 줄인다.
        승인 업무 전체를 잠그는 용도는 아니며, DB 처리는 connect가 담당한다.
        """
        with self._activity:
            self._active += 1
        try:
            yield
        finally:
            with self._activity:
                self._active -= 1

    def reset(self, clear_sessions) -> bool:
        """진행 중인 요청이 없을 때 시작 데이터를 복원하고 접속을 해제한다.

        clear_sessions는 이 공간의 세션을 지우는 함수다.
        초기화를 마치면 True, 요청 처리 중이라 실행하지 못하면 False를 반환한다.
        """
        with self._activity:
            if self._active:
                return False
            with self.connect() as db:
                db.execute("DELETE FROM orders")
                db.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", SEEDS)
            clear_sessions()
            return True

    def list_orders(self, corp_id: str) -> list[dict]:
        """전달받은 회사의 발주만 조회해 딕셔너리 목록으로 반환한다.

        API는 corp_id에 서버가 확인한 사용자 회사를 전달한다.
        """
        with self.connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM orders WHERE corp_id = ? ORDER BY id", (corp_id,)
            )]

    def find_order(self, order_id: int, corp_id: str) -> dict | None:
        """발주 번호와 회사가 모두 일치하는 발주를 반환하고, 없으면 None을 반환한다."""
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM orders WHERE id = ? AND corp_id = ?", (order_id, corp_id)
            ).fetchone()
            return dict(row) if row else None

    def approve_order(self, order_id: int, user, check_permission) -> dict | None:
        """사용자 회사의 발주를 찾아 업무 판단을 통과한 경우에만 승인을 저장한다.

        user는 서버가 확인한 사용자이며, check_permission은 승인 가능 여부를
        판단하는 함수다. 이 함수가 예외를 발생시키면 UPDATE까지 진행하지 않는다.
        조회·판단·갱신은 하나의 트랜잭션에서 수행한다. 저장 시 조회했던 값도
        비교하고, 성공하면 갱신된 발주를 반환한다. 대상이 없으면 None을 반환한다.
        """
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM orders WHERE id = ? AND corp_id = ?", (order_id, user.corp_id)
            ).fetchone()
            if row is None:
                return None
            order = dict(row)
            # A rule failure raises before either write; the connection rolls back.
            check_permission(user, order)
            changed = db.execute(
                """UPDATE orders SET status = 'APPROVED', approval_count = approval_count + 1
                   WHERE id = ? AND corp_id = ? AND status = ? AND approval_count = ?""",
                (order_id, user.corp_id, order["status"], order["approval_count"]),
            )
            if changed.rowcount != 1:
                raise RuntimeError("Order changed before approval")
            return dict(db.execute("SELECT * FROM orders WHERE id = ? AND corp_id = ?",
                                   (order_id, user.corp_id)).fetchone())
