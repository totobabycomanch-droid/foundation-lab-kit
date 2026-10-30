"""실제 HTTP 연결과 관찰 결과 검사. 실행 중인 독자 서버는 사용하지 않는다."""
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web_server import create_server

PATHS = {
    "PENDING": (), "APPROVED": ("approve",),
    "SHIPPING": ("approve", "ship"),
    "DELIVERED": ("approve", "ship", "confirm_delivery"),
    "COMPLETED": ("approve", "ship", "confirm_delivery", "complete"),
    "CANCELLED": ("cancel",),
}
EXPECTED = {
    ("PENDING", "approve"): "APPROVED", ("PENDING", "cancel"): "CANCELLED",
    ("APPROVED", "ship"): "SHIPPING", ("SHIPPING", "confirm_delivery"): "DELIVERED",
    ("DELIVERED", "complete"): "COMPLETED",
}


class WebTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server(0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, path, data=None, headers=None):
        url = f"http://127.0.0.1:{self.server.server_port}{path}"
        request = Request(url, data=None if data is None else json.dumps(data).encode(),
                          headers={"Content-Type": "application/json", **(headers or {})})
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as error:
            response = error
        with response:
            raw = response.read()
            return response.status, json.loads(raw) if "application/json" in response.headers.get("Content-Type", "") else raw

    def new(self):
        status, data = self.request("/api/new", {})
        self.assertEqual(status, 200, data)
        self.assertEqual(data["state"], "PENDING")
        return data["session"]

    def act(self, key, action):
        return self.request("/api/action", {"session": key, "action": action})

    def test_all_thirty_state_action_pairs(self):
        """HTTP의 오류와 실제 객체 상태를 각각 확인한다."""
        for state, steps in PATHS.items():
            for action in ("approve", "ship", "confirm_delivery", "complete", "cancel"):
                with self.subTest(state=state, action=action):
                    key = self.new()
                    for step in steps:
                        self.assertEqual(self.act(key, step)[0], 200)
                    status, data = self.act(key, action)
                    expected = EXPECTED.get((state, action))
                    self.assertEqual(status, 200 if expected else 409)
                    self.assertEqual(data["before"], state)
                    self.assertEqual(data["after"], expected or state)
                    self.assertEqual(data["exception"], None if expected else "ValueError")
                    self.assertEqual(self.request("/api/state?session=" + key)[1]["state"], expected or state)

    def test_independent_orders_and_requery(self):
        first, second = self.new(), self.new()
        self.act(first, "approve")
        self.act(second, "cancel")
        self.assertEqual(self.request("/api/state?session=" + first)[1]["state"], "APPROVED")
        self.assertEqual(self.request("/api/state?session=" + second)[1]["state"], "CANCELLED")

    def test_invalid_requests_do_not_change_order(self):
        key = self.new()
        self.assertEqual(self.act(key, "_status")[0], 422)
        self.assertEqual(self.request("/api/action", {"session": [], "action": "approve"})[0], 404)
        self.assertEqual(self.request("/api/new", {}, {"Origin": "http://other.invalid"})[0], 403)
        self.assertEqual(self.request("/api/state?session=" + key)[1]["state"], "PENDING")

    def test_static_screen_and_missing_session(self):
        for path in ("/", "/app.js", "/style.css"):
            self.assertEqual(self.request(path)[0], 200)
        self.assertEqual(self.request("/api/state?session=missing")[0], 404)

    def test_observer_does_not_hide_mutation_before_error(self):
        """거부 전에 값을 바꾸는 결함을 관찰 서버가 복구하지 않아야 한다."""
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "broken.py"
            source.write_text('class Order:\n    def __init__(self, order_id):\n        self.order_id = order_id\n        self.status = "PENDING"\n    def ship(self):\n        self.status = "SHIPPING"\n        raise ValueError("거부 전에 잘못 변경")\n', encoding="utf-8")
            self.server.shutdown()
            self.server.server_close()
            self.thread.join()
            self.server = create_server(0, source)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            key = self.new()
            status, data = self.act(key, "ship")
            self.assertEqual(status, 409)
            self.assertEqual(data["before"], "PENDING")
            self.assertEqual(data["after"], "SHIPPING")
            self.assertEqual(self.request("/api/state?session=" + key)[1]["state"], "SHIPPING")


if __name__ == "__main__":
    unittest.main(verbosity=2)
