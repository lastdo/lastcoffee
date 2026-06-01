from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import argparse
import json
import mimetypes


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
STATE_FILE = DATA_DIR / "census.json"
PORT = 8000


class CensusHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/api/state":
            self.send_json(read_state())
            return
        super().do_GET()

    def do_PUT(self):
        if self.path.split("?", 1)[0] != "/api/state":
            self.send_error(404)
            return

        try:
            payload = self.read_json_body()
            write_state(payload)
            self.send_json({"ok": True})
        except ValueError as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=400)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 2_000_000:
            raise ValueError("payload too large")
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("invalid json") from exc
        validate_state(payload)
        return payload

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def end_headers(self):
        if self.path.endswith(".js"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()


def read_state():
    if not STATE_FILE.exists():
        return {"brands": [], "entries": []}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = STATE_FILE.with_suffix(".broken.json")
        STATE_FILE.replace(backup)
        return {"brands": [], "entries": []}


def write_state(payload):
    DATA_DIR.mkdir(exist_ok=True)
    temp_file = STATE_FILE.with_suffix(".tmp")
    temp_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_file.replace(STATE_FILE)


def validate_state(payload):
    if not isinstance(payload, dict):
        raise ValueError("state must be an object")
    if not isinstance(payload.get("brands", []), list):
        raise ValueError("brands must be a list")
    if not isinstance(payload.get("entries", []), list):
        raise ValueError("entries must be a list")


def main():
    parser = argparse.ArgumentParser(description="Run the Bahamut audio census form server.")
    parser.add_argument("--public", action="store_true", help="bind to 0.0.0.0 for LAN access")
    parser.add_argument("--port", type=int, default=PORT, help="server port")
    args = parser.parse_args()
    host = "0.0.0.0" if args.public else "127.0.0.1"

    mimetypes.add_type("text/javascript; charset=utf-8", ".js")
    mimetypes.add_type("text/css; charset=utf-8", ".css")
    server = ThreadingHTTPServer((host, args.port), CensusHandler)
    print(f"巴哈耳機普查表單已啟動：http://localhost:{args.port}")
    if args.public:
        print(f"區網模式已開啟：請讓使用者連到這台主機 IP 的 :{args.port}")
    else:
        print("目前只允許本機連線；分享給區網使用者時請加 --public。")
    server.serve_forever()


if __name__ == "__main__":
    main()
