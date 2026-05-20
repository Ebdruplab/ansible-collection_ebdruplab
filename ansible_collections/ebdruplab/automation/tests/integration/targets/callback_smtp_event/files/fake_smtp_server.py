import argparse
import json
import re
import socketserver
from pathlib import Path
from typing import Dict
from typing import List
from typing import Optional


ADDRESS_RE = re.compile(r"<([^>]+)>")


def _extract_address(command: str) -> str:
    match = ADDRESS_RE.search(command)
    if match:
        return match.group(1)

    return command.split(":", 1)[-1].strip()


class FakeSMTPServer(socketserver.TCPServer):
    allow_reuse_address = True

    def __init__(self, server_address, request_handler_class, output_dir: Path):
        super().__init__(server_address, request_handler_class)
        self.output_dir = output_dir
        self.capture: Optional[Dict[str, object]] = None

    def save_capture(self, mail_from: str, rcpt_tos: List[str], data_lines: List[str]) -> None:
        message = "\n".join(data_lines) + "\n"
        message_file = self.output_dir / "message.eml"
        capture_file = self.output_dir / "capture.json"

        message_file.write_text(message, encoding="utf-8")

        self.capture = {
            "mail_from": mail_from,
            "rcpt_tos": rcpt_tos,
            "message_file": str(message_file),
            "message": message,
        }
        capture_file.write_text(json.dumps(self.capture, indent=2, sort_keys=True), encoding="utf-8")


class SMTPHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        mail_from = ""
        rcpt_tos: List[str] = []
        data_lines: List[str] = []
        in_data = False

        self._send("220 fake-smtp ESMTP ready")

        while True:
            raw_line = self.rfile.readline()
            if not raw_line:
                break

            line = raw_line.decode("utf-8", "replace").rstrip("\r\n")
            upper_line = line.upper()

            if in_data:
                if line == ".":
                    self.server.save_capture(mail_from=mail_from, rcpt_tos=rcpt_tos, data_lines=data_lines)
                    self._send("250 2.0.0 OK")
                    in_data = False
                    continue

                if line.startswith(".."):
                    line = line[1:]

                data_lines.append(line)
                continue

            if upper_line.startswith("EHLO") or upper_line.startswith("HELO"):
                self._send_multiline(
                    [
                        "250-fake-smtp",
                        "250-PIPELINING",
                        "250 HELP",
                    ]
                )
                continue

            if upper_line.startswith("MAIL FROM:"):
                mail_from = _extract_address(line)
                self._send("250 2.1.0 OK")
                continue

            if upper_line.startswith("RCPT TO:"):
                rcpt_tos.append(_extract_address(line))
                self._send("250 2.1.5 OK")
                continue

            if upper_line == "DATA":
                data_lines = []
                in_data = True
                self._send("354 End data with <CR><LF>.<CR><LF>")
                continue

            if upper_line == "RSET":
                mail_from = ""
                rcpt_tos = []
                data_lines = []
                in_data = False
                self._send("250 2.0.0 OK")
                continue

            if upper_line == "QUIT":
                self._send("221 2.0.0 Bye")
                break

            self._send("250 2.0.0 OK")

    def _send(self, line: str) -> None:
        self.wfile.write((line + "\r\n").encode("ascii"))

    def _send_multiline(self, lines: List[str]) -> None:
        for line in lines:
            self._send(line)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--port-file", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with FakeSMTPServer(("127.0.0.1", 0), SMTPHandler, output_dir=output_dir) as server:
        server.timeout = 30
        Path(args.port_file).write_text(str(server.server_address[1]), encoding="utf-8")
        server.handle_request()

        if not server.capture:
            raise SystemExit("No SMTP message was captured")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
