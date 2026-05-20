import importlib.util
import json
import pathlib
import unittest


PLUGIN_PATH = (
    pathlib.Path(__file__).resolve().parents[4] / "plugins" / "callback" / "http_event.py"
)
PLUGIN_SPEC = importlib.util.spec_from_file_location("http_event", PLUGIN_PATH)
HTTP_EVENT = importlib.util.module_from_spec(PLUGIN_SPEC)
assert PLUGIN_SPEC is not None and PLUGIN_SPEC.loader is not None
PLUGIN_SPEC.loader.exec_module(HTTP_EVENT)
CallbackModule = HTTP_EVENT.CallbackModule


class FakeStats:
    def __init__(self, summaries):
        self._summaries = summaries
        self.processed = {host: True for host in summaries}

    def summarize(self, host):
        return self._summaries[host]


class FakeDisplay:
    def __init__(self):
        self.vvv_messages = []
        self.warning_messages = []

    def vvv(self, message):
        self.vvv_messages.append(message)

    def warning(self, message):
        self.warning_messages.append(message)


class HttpEventCallbackTests(unittest.TestCase):
    def _plugin(self, options=None):
        plugin = CallbackModule()
        plugin._display = FakeDisplay()
        option_values = options or {}

        def get_option(name):
            return option_values.get(name)

        plugin.get_option = get_option
        return plugin

    def test_v2_playbook_on_stats_builds_failure_request(self):
        plugin = self._plugin(
            {
                "enabled": True,
                "failure_url": "https://example.invalid/failure",
                "auth_token": "secret-token",
                "auth_header": "X-Auth-Token",
                "auth_scheme": "Token",
                "status_header": "X-Job-Status",
                "host_header": "X-Affected-Hosts",
                "extra_headers": "X-Source=ansible,X-Environment=test",
            }
        )
        stats = FakeStats(
            {
                "db1": {"ok": 2, "changed": 0, "unreachable": 0, "failures": 0},
                "web1": {"ok": 1, "changed": 1, "unreachable": 0, "failures": 1},
            }
        )
        captured = {}

        def fake_send_request(url, headers, body):
            captured["url"] = url
            captured["headers"] = headers
            captured["body"] = body

        plugin._send_request = fake_send_request

        plugin.v2_playbook_on_stats(stats)

        self.assertEqual(captured["url"], "https://example.invalid/failure")
        self.assertEqual(captured["headers"]["X-Auth-Token"], "Token secret-token")
        self.assertEqual(captured["headers"]["X-Job-Status"], "failure")
        self.assertEqual(captured["headers"]["X-Affected-Hosts"], "web1")
        self.assertEqual(captured["headers"]["X-Source"], "ansible")
        self.assertEqual(captured["headers"]["X-Environment"], "test")

        payload = json.loads(captured["body"].decode("utf-8"))
        self.assertEqual(payload["status"], "failure")
        self.assertEqual(payload["hosts"], ["web1"])
        self.assertEqual(payload["failed_hosts"], ["web1"])
        self.assertEqual(payload["unreachable_hosts"], [])
        self.assertEqual(payload["ok_hosts"], ["db1", "web1"])
        self.assertEqual(payload["changed_hosts"], ["web1"])

    def test_build_headers_uses_raw_token_and_build_body_can_be_disabled(self):
        plugin = self._plugin(
            {
                "auth_token": "raw-token",
                "auth_header": "X-Auth",
                "auth_scheme": "",
                "status_header": "X-Status",
                "host_header": "X-Hosts",
                "send_body": False,
            }
        )
        stats = FakeStats(
            {
                "web1": {"ok": 1, "changed": 0, "unreachable": 0, "failures": 0},
                "web2": {"ok": 1, "changed": 0, "unreachable": 0, "failures": 0},
            }
        )

        headers = plugin._build_headers(status="success", hosts=["web2", "web1", "web2"])
        body = plugin._build_body(status="success", hosts=["web1", "web2"], stats=stats)

        self.assertEqual(headers["X-Auth"], "raw-token")
        self.assertEqual(headers["X-Status"], "success")
        self.assertEqual(headers["X-Hosts"], "web1,web2")
        self.assertIsNone(body)


if __name__ == "__main__":
    unittest.main()
