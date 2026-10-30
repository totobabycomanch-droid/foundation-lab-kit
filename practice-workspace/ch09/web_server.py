"""표준 라이브러리 관찰 서버. 상태 판단은 학습자의 Order에 맡긴다."""
import argparse
import importlib.util
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
ACTIONS = ("approve", "ship", "confirm_delivery", "complete", "cancel")


def create_server(port=8309, order_file=None):
    """서버마다 별도 주문 저장소를 만든다. 재시작하면 객체는 사라진다."""
    orders = {}
    source = Path(order_file) if order_file else ROOT / "erp-mini/domain/order.py"
    order_type = None

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, data):
            raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            parsed = urlsplit(self.path)
            if parsed.path == "/api/state":
                key = parse_qs(parsed.query).get("session", [""])[0]
                if key not in orders:
                    self.reply(404, {"detail": "주문이 없습니다. 새 주문을 만드세요."})
                    return
                order = orders[key]
                self.reply(200, {"order_id": order.order_id, "state": order.status})
                return
            files = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"), "/style.css": ("style.css", "text/css")}
            if parsed.path not in files:
                self.reply(404, {"detail": "경로를 찾을 수 없습니다."})
                return
            name, mime = files[parsed.path]
            raw = (ROOT / "frontend" / name).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime + "; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            nonlocal order_type
            host = self.headers.get("Host", "")
            origin = self.headers.get("Origin")
            if origin and origin != "http://" + host:
                self.reply(403, {"detail": "다른 사이트의 요청은 받지 않습니다."})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 8192:
                    raise ValueError()
                if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    raise ValueError()
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError()
            except (ValueError, TypeError):
                self.reply(422, {"detail": "JSON 입력 형식을 확인하세요."})
                return
            path = urlsplit(self.path).path
            if path == "/api/new":
                if len(orders) >= 200:
                    self.reply(503, {"detail": "실습 서버를 재시작한 뒤 새 주문을 만드세요."})
                    return
                try:
                    if order_type is None:
                        spec = importlib.util.spec_from_file_location("ch09_observed_order", source)
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[spec.name] = module
                        spec.loader.exec_module(module)
                        order_type = module.Order
                    order = order_type(order_id=len(orders) + 1)
                    state = order.status
                except Exception as error:
                    self.reply(501, {"detail": "주문 구현을 확인하세요: " + type(error).__name__})
                    return
                key = str(uuid4())
                orders[key] = order
                self.reply(200, {"session": key, "order_id": order.order_id, "state": state})
                return
            if path != "/api/action":
                self.reply(404, {"detail": "경로를 찾을 수 없습니다."})
                return
            key, action = data.get("session"), data.get("action")
            if not isinstance(key, str) or key not in orders:
                self.reply(404, {"detail": "주문이 없습니다. 새 주문을 만드세요."})
                return
            if action not in ACTIONS:
                self.reply(422, {"detail": "제공된 행동을 선택하세요."})
                return
            order = orders[key]
            before = order.status
            result = {"order_id": order.order_id, "action": action, "before": before, "exception": None, "detail": "행동을 실행했습니다."}
            status = 200
            try:
                getattr(order, action)()
            except ValueError as error:
                status = 409
                result.update(exception="ValueError", detail=str(error))
            except Exception as error:
                status = 500
                result.update(exception=type(error).__name__, detail="업무 코드 오류를 확인하세요: " + str(error))
            # 실패한 객체도 그대로 읽는다. 복원하거나 새 객체로 교체하지 않는다.
            result.update(after=order.status, status_code=status)
            self.reply(status, result)

    return HTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8309)
    args = parser.parse_args()
    server = create_server(args.port)
    print(f"Open http://127.0.0.1:{server.server_port} ; stop with Ctrl+C.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
