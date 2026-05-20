import argparse
import json
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from pathlib import Path
from typing import Dict
from typing import Optional


class FakeHTTPServer(HTTPServer):
    allow_reuse_address = True

    def __init__(self, server_address, request_handler_class, output_dir: Path):
        super().__init__(server_address, request_handler_class)
        self.output_dir = output_dir
        self.capture: Optional[Dict[str, object]] = None

    def save_capture(self, handler: BaseHTTPRequestHandler, body: bytes) -> None:
        capture = {
            "method": handler.command,
            "path": handler.path,
            "headers": dict(handler.headers.items()),
            "body": body.decode("utf-8"),
        }
        self.capture = capture
        (self.output_dir / "capture.json").write_text(
            json.dumps(capture, indent=2, sort_keys=True),
            encoding="utf-8",
        )


class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        self._handle()

    def do_PUT(self) -> None:
        self._handle()

    def do_PATCH(self) -> None:
        self._handle()

    def log_message(self, format, *args) -> None:
        return

    def _handle(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        self.server.save_capture(self, body)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--port-file", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with FakeHTTPServer(("127.0.0.1", 0), RequestHandler, output_dir=output_dir) as server:
        Path(args.port_file).write_text(str(server.server_address[1]), encoding="utf-8")
        server.handle_request()

        if not server.capture:
            raise SystemExit("No HTTP request was captured")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
