import importlib.util
import pathlib
import unittest


PLUGIN_PATH = (
    pathlib.Path(__file__).resolve().parents[4] / "plugins" / "callback" / "smtp_event.py"
)
PLUGIN_SPEC = importlib.util.spec_from_file_location("smtp_event", PLUGIN_PATH)
SMTP_EVENT = importlib.util.module_from_spec(PLUGIN_SPEC)
assert PLUGIN_SPEC is not None and PLUGIN_SPEC.loader is not None
PLUGIN_SPEC.loader.exec_module(SMTP_EVENT)
CallbackModule = SMTP_EVENT.CallbackModule


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


class FakeSMTP:
    def __init__(self):
        self.message = None
        self.from_addr = None
        self.to_addrs = None
        self.quit_called = False

    def send_message(self, message, from_addr, to_addrs):
        self.message = message
        self.from_addr = from_addr
        self.to_addrs = to_addrs

    def quit(self):
        self.quit_called = True


class SmtpEventCallbackTests(unittest.TestCase):
    def _plugin(self, options=None):
        plugin = CallbackModule()
        plugin._display = FakeDisplay()
        option_values = options or {}

        def get_option(name):
            return option_values.get(name)

        plugin.get_option = get_option
        return plugin

    def test_v2_playbook_on_stats_builds_failure_report_and_dispatches_mail(self):
        plugin = self._plugin(
            {
                "enabled": True,
                "failure": True,
                "sender": "Ansible <ansible@example.com>",
                "to": "ops@example.com",
                "subject_prefix": "[Ansible Ebdruplab]",
                "send_event_dump": True,
            }
        )
        plugin._playbook_name = "site.yml"
        plugin._play_names = ["Deploy app"]
        plugin._target_hosts = ["web1", "db1"]
        plugin._last_task = {
            "name": "Install package",
            "action": "apt",
            "path": "/repo/site.yml",
            "line": 42,
        }
        plugin._events = [
            {
                "event": "failure",
                "host": "web1",
                "play": "Deploy app",
                "task": "Install package",
                "module": "apt",
                "path": "/repo/site.yml",
                "line": 42,
                "item": None,
                "message": "package install failed\nfull traceback",
                "stdout": None,
                "stderr": "apt stderr",
                "exception": None,
                "result": {"msg": "package install failed"},
            }
        ]
        stats = FakeStats(
            {
                "db1": {"ok": 3, "changed": 0, "unreachable": 0, "failures": 0},
                "web1": {"ok": 1, "changed": 1, "unreachable": 0, "failures": 1},
            }
        )
        captured = {}

        def fake_send_mail(sender, subject, body):
            captured["sender"] = sender
            captured["subject"] = subject
            captured["body"] = body

        plugin._send_mail = fake_send_mail

        plugin.v2_playbook_on_stats(stats)

        self.assertEqual(captured["sender"], "Ansible <ansible@example.com>")
        self.assertEqual(
            captured["subject"],
            "[Ansible Ebdruplab] FAILURE - Deploy app - site.yml - web1",
        )
        self.assertIn("Result: failure", captured["body"])
        self.assertIn(
            "Failure on web1 at task 'Install package': package install failed",
            captured["body"],
        )
        self.assertIn("Affected hosts: web1", captured["body"])
        self.assertIn("Last task: Install package (apt) in /repo/site.yml:42", captured["body"])
        self.assertIn("Captured event dump", captured["body"])

    def test_send_mail_uses_bcc_only_for_envelope_recipients(self):
        plugin = self._plugin(
            {
                "to": "Ops <ops@example.com>",
                "cc": "Platform <platform@example.com>",
                "bcc": "Audit <audit@example.com>",
                "message_id_domain": "example.com",
            }
        )
        fake_smtp = FakeSMTP()
        plugin._connect_smtp = lambda: fake_smtp

        plugin._send_mail(
            sender="Ansible <ansible@example.com>",
            subject="Deployment report",
            body="Everything is fine.",
        )

        self.assertIsNotNone(fake_smtp.message)
        self.assertEqual(fake_smtp.from_addr, "ansible@example.com")
        self.assertEqual(
            fake_smtp.to_addrs,
            ["ops@example.com", "platform@example.com", "audit@example.com"],
        )
        self.assertEqual(fake_smtp.message["To"], "Ops <ops@example.com>")
        self.assertEqual(fake_smtp.message["Cc"], "Platform <platform@example.com>")
        self.assertIsNone(fake_smtp.message["Bcc"])
        self.assertEqual(fake_smtp.message["Subject"], "Deployment report")
        self.assertIn("Everything is fine.", fake_smtp.message.get_content())
        self.assertTrue(fake_smtp.quit_called)


if __name__ == "__main__":
    unittest.main()
