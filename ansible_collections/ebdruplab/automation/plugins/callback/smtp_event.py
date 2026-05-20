# -*- coding: utf-8 -*-
# Copyright (c) 2026, Kristian Ebdrup
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
name: smtp_event
short_description: Send one Ansible playbook result report by SMTP email
description:
  - Sends one email report when an Ansible playbook finishes.
  - Reports success, failure, or unreachable status.
  - Includes playbook name, play name, target hosts, affected hosts, last task, and captured error details.
  - Supports a configurable email subject prefix such as C([Ansible Ebdruplab]).
  - Supports SMTP authentication, STARTTLS, SMTP-over-SSL, CC, and BCC.
  - Supports configuration from ansible.cfg and environment variables.
type: aggregate
requirements:
  - ansible-core
options:
  enabled:
    description:
      - Enables or disables the callback plugin.
    type: bool
    default: false
    ini:
      - section: callback_smtp_event
        key: enabled
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_ENABLED

  success:
    description:
      - Send the final email report when the playbook completes successfully.
    type: bool
    default: true
    ini:
      - section: callback_smtp_event
        key: success
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_SUCCESS

  failure:
    description:
      - Send the final email report when one or more hosts fail.
    type: bool
    default: true
    ini:
      - section: callback_smtp_event
        key: failure
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_FAILURE

  unreachable:
    description:
      - Send the final email report when one or more hosts are unreachable.
    type: bool
    default: true
    ini:
      - section: callback_smtp_event
        key: unreachable
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_UNREACHABLE

  smtp_host:
    description:
      - SMTP server hostname or IP address.
    type: str
    default: localhost
    ini:
      - section: callback_smtp_event
        key: smtp_host
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_SMTP_HOST

  smtp_port:
    description:
      - SMTP server port.
      - Common values are C(25) for plain SMTP, C(587) for STARTTLS, and C(465) for SMTP-over-SSL.
    type: int
    default: 25
    ini:
      - section: callback_smtp_event
        key: smtp_port
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_SMTP_PORT

  sender:
    description:
      - Email sender address.
      - 'Example: C(Ansible <ansible@example.com>).'
    type: str
    required: true
    ini:
      - section: callback_smtp_event
        key: sender
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_SENDER

  to:
    description:
      - Email recipients.
      - Format is comma-separated addresses.
      - 'Example: C(ops@example.com,platform@example.com).'
    type: str
    required: false
    ini:
      - section: callback_smtp_event
        key: to
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_TO

  cc:
    description:
      - Email CC recipients.
      - Format is comma-separated addresses.
    type: str
    required: false
    ini:
      - section: callback_smtp_event
        key: cc
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_CC

  bcc:
    description:
      - Email BCC recipients.
      - Format is comma-separated addresses.
      - BCC recipients are used as SMTP envelope recipients but are not added to message headers.
    type: str
    required: false
    ini:
      - section: callback_smtp_event
        key: bcc
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_BCC

  username:
    description:
      - SMTP authentication username.
      - No SMTP authentication is attempted when this value is empty.
    type: str
    required: false
    ini:
      - section: callback_smtp_event
        key: username
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_USERNAME

  password:
    description:
      - SMTP authentication password.
      - Use an environment variable or Ansible Vault instead of committing this value to ansible.cfg.
    type: str
    required: false
    ini:
      - section: callback_smtp_event
        key: password
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_PASSWORD

  starttls:
    description:
      - Upgrade the SMTP connection using STARTTLS before authentication.
      - Commonly used with port C(587).
      - Do not enable together with C(use_ssl).
    type: bool
    default: false
    ini:
      - section: callback_smtp_event
        key: starttls
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_STARTTLS

  use_ssl:
    description:
      - Use SMTP-over-SSL from the start of the connection.
      - Commonly used with port C(465).
      - Do not enable together with C(starttls).
    type: bool
    default: false
    ini:
      - section: callback_smtp_event
        key: use_ssl
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_USE_SSL

  validate_certs:
    description:
      - Validate TLS certificates when using STARTTLS or SMTP-over-SSL.
    type: bool
    default: true
    ini:
      - section: callback_smtp_event
        key: validate_certs
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_VALIDATE_CERTS

  timeout:
    description:
      - SMTP connection timeout in seconds.
    type: int
    default: 30
    ini:
      - section: callback_smtp_event
        key: timeout
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_TIMEOUT

  subject_prefix:
    description:
      - Prefix added to generated email subjects.
      - 'Example: C([Ansible Ebdruplab]).'
      - Use an empty value to disable subject prefixing.
    type: str
    default: '[Ansible]'
    ini:
      - section: callback_smtp_event
        key: subject_prefix
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_SUBJECT_PREFIX

  message_id_domain:
    description:
      - Domain name used for the Message-ID header.
      - The default is the hostname of the control node.
    type: str
    required: false
    ini:
      - section: callback_smtp_event
        key: message_id_domain
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_MESSAGE_ID_DOMAIN

  send_event_dump:
    description:
      - Include a JSON dump of captured failure and unreachable events in the final report.
    type: bool
    default: false
    ini:
      - section: callback_smtp_event
        key: send_event_dump
    env:
      - name: EBDRUPLAB_AUTOMATION_SMTP_EVENT_SEND_EVENT_DUMP
"""

import email.utils
import json
import os
import smtplib
import socket
import ssl
from email.message import EmailMessage
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple

from ansible.module_utils.common.text.converters import to_text
from ansible.parsing.ajson import AnsibleJSONEncoder
from ansible.plugins.callback import CallbackBase

CALLBACK_VERSION = 2.0
CALLBACK_TYPE = "aggregate"
CALLBACK_NAME = "ebdruplab.automation.smtp_event"
CALLBACK_NEEDS_ENABLED = True


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = CALLBACK_VERSION
    CALLBACK_TYPE = CALLBACK_TYPE
    CALLBACK_NAME = CALLBACK_NAME
    CALLBACK_NEEDS_ENABLED = CALLBACK_NEEDS_ENABLED

    def __init__(self) -> None:
        super().__init__()
        self._options_loaded = False
        self._playbook_name = "unknown"
        self._play_names: List[str] = []
        self._target_hosts: List[str] = []
        self._last_task: Optional[Dict[str, Any]] = None
        self._events: List[Dict[str, Any]] = []

    def set_options(
        self,
        task_keys: Optional[Dict[str, Any]] = None,
        var_options: Optional[Dict[str, Any]] = None,
        direct: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().set_options(task_keys=task_keys, var_options=var_options, direct=direct)
        self._options_loaded = True

    def v2_playbook_on_start(self, playbook: Any) -> None:
        playbook_file = getattr(playbook, "_file_name", None)
        self._playbook_name = os.path.basename(playbook_file) if playbook_file else "unknown"
        self._play_names = []
        self._target_hosts = []
        self._last_task = None
        self._events = []

    def v2_playbook_on_play_start(self, play: Any) -> None:
        play_name = self._play_name(play)
        if play_name and play_name not in self._play_names:
            self._play_names.append(play_name)

        for host in self._hosts_from_play(play):
            self._remember_host(host)

    def v2_playbook_on_task_start(self, task: Any, is_conditional: bool = False) -> None:
        self._last_task = self._task_details(task)

    def v2_playbook_on_handler_task_start(self, task: Any) -> None:
        self._last_task = self._task_details(task)

    def v2_runner_on_ok(self, result: Any) -> None:
        self._remember_host_from_result(result)

    def v2_runner_on_skipped(self, result: Any) -> None:
        self._remember_host_from_result(result)

    def v2_runner_on_failed(self, result: Any, ignore_errors: bool = False) -> None:
        self._remember_host_from_result(result)

        if not ignore_errors:
            self._events.append(self._event_details(result=result, event="failure"))

    def v2_runner_on_unreachable(self, result: Any) -> None:
        self._remember_host_from_result(result)
        self._events.append(self._event_details(result=result, event="unreachable"))

    def v2_runner_on_async_failed(self, result: Any) -> None:
        self._remember_host_from_result(result)
        self._events.append(self._event_details(result=result, event="failure"))

    def v2_runner_item_on_failed(self, result: Any) -> None:
        self._remember_host_from_result(result)
        self._events.append(self._event_details(result=result, event="failure"))

    def v2_playbook_on_stats(self, stats: Any) -> None:
        self._ensure_options_loaded()

        if not self._get_bool("enabled"):
            return

        status = self._determine_status(stats)

        if not self._get_bool(status, default=True):
            self._display.vvv(
                "ebdruplab.automation.smtp_event: report disabled for status '%s'" % status
            )
            return

        sender = self._get_str("sender")
        if not sender:
            self._display.warning("ebdruplab.automation.smtp_event: sender is required")
            return

        if not self._addresses_from_options(["to", "cc", "bcc"]):
            self._display.warning("ebdruplab.automation.smtp_event: no recipient configured")
            return

        subject = self._build_subject(status=status, stats=stats)
        body = self._build_report(status=status, stats=stats)
        self._send_mail(sender=sender, subject=subject, body=body)

    def _ensure_options_loaded(self) -> None:
        if not self._options_loaded:
            try:
                self.set_options()
            except Exception:
                pass

    def _determine_status(self, stats: Any) -> str:
        failed_hosts = self._hosts_with_count(stats=stats, key="failures")
        unreachable_hosts = self._hosts_with_count(stats=stats, key="unreachable")

        if failed_hosts:
            return "failure"

        if unreachable_hosts:
            return "unreachable"

        return "success"

    def _build_subject(self, status: str, stats: Any) -> str:
        prefix = self._get_str("subject_prefix") or ""
        play_name = self._current_play_name()
        affected_hosts = self._affected_hosts_for_status(status=status, stats=stats)

        subject = "%s - %s - %s - %s" % (
            status.upper(),
            play_name,
            self._playbook_name,
            self._short_list(affected_hosts, limit=4),
        )

        if prefix:
            return "%s %s" % (prefix, subject)

        return subject

    def _build_report(self, status: str, stats: Any) -> str:
        all_hosts = sorted(stats.processed.keys())
        failed_hosts = self._hosts_with_count(stats=stats, key="failures")
        unreachable_hosts = self._hosts_with_count(stats=stats, key="unreachable")
        affected_hosts = self._affected_hosts_for_status(status=status, stats=stats)
        relevant_events = self._events_for_status(status=status)

        body = "Ansible report\n"
        body += "==============\n\n"
        body += "Result: %s\n" % status
        body += "Summary: %s\n\n" % self._summary_sentence(
            status=status,
            affected_hosts=affected_hosts,
            events=relevant_events,
        )

        body += "Context\n"
        body += "-------\n"
        body += "Playbook: %s\n" % self._playbook_name
        body += "Play: %s\n" % self._current_play_name()
        body += "All plays: %s\n" % self._format_list(self._play_names)
        body += "Targets in play: %s\n" % self._format_list(self._target_hosts or all_hosts)
        body += "Last task: %s\n\n" % self._task_one_line(self._last_task)

        body += "Hosts\n"
        body += "-----\n"
        body += "All hosts: %s\n" % self._format_list(all_hosts)
        body += "Affected hosts: %s\n" % self._format_list(affected_hosts)
        body += "Failed hosts: %s\n" % self._format_list(failed_hosts)
        body += "Unreachable hosts: %s\n\n" % self._format_list(unreachable_hosts)

        body += "What happened\n"
        body += "-------------\n"
        body += self._what_happened(status=status, events=relevant_events)
        body += "\n"

        body += "Recap\n"
        body += "-----\n"
        for host in all_hosts:
            body += "%s: %s\n" % (host, self._recap_line(stats.summarize(host)))

        if self._get_bool("send_event_dump", default=False) and relevant_events:
            body += "\nCaptured event dump\n"
            body += "-------------------\n"
            body += self._indent(
                json.dumps(relevant_events, cls=AnsibleJSONEncoder, indent=4, sort_keys=True)
            )
            body += "\n"

        return body

    def _summary_sentence(
        self,
        status: str,
        affected_hosts: List[str],
        events: List[Dict[str, Any]],
    ) -> str:
        if status == "success":
            return "Playbook completed successfully on %s." % self._format_list(affected_hosts)

        if status == "unreachable":
            return "One or more hosts were unreachable: %s." % self._format_list(affected_hosts)

        first = events[0] if events else {}
        task = first.get("task") or self._task_one_line(self._last_task)
        message = first.get("message")

        if message:
            return "Failure on %s at task '%s': %s" % (
                self._format_list(affected_hosts),
                task,
                self._first_line(message),
            )

        return "Failure on %s at task '%s'." % (self._format_list(affected_hosts), task)

    def _what_happened(self, status: str, events: List[Dict[str, Any]]) -> str:
        if status == "success":
            return "No failures or unreachable hosts were recorded.\n"

        if not events:
            return "Ansible reported status '%s', but no detailed event was captured. Check the recap above.\n" % status

        lines = ""
        for event in events:
            lines += "- Host: %s\n" % event.get("host", "unknown")
            lines += "  Event: %s\n" % event.get("event", status)
            lines += "  Play: %s\n" % event.get("play", "unknown")
            lines += "  Task: %s\n" % event.get("task", "unknown")
            lines += "  Module: %s\n" % event.get("module", "unknown")

            if event.get("path"):
                lines += "  Path: %s\n" % event.get("path")

            if event.get("line"):
                lines += "  Line: %s\n" % event.get("line")

            if event.get("item") is not None:
                lines += "  Item: %s\n" % event.get("item")

            if event.get("message"):
                lines += "  Message: %s\n" % self._first_line(event.get("message"))

            if event.get("stderr"):
                lines += "  Stderr: %s\n" % self._first_line(event.get("stderr"))

            lines += "\n"

        return lines

    def _events_for_status(self, status: str) -> List[Dict[str, Any]]:
        if status == "success":
            return []

        return [event for event in self._events if event.get("event") == status]

    def _event_details(self, result: Any, event: str) -> Dict[str, Any]:
        task = getattr(result, "_task", None)
        result_data = getattr(result, "_result", {})
        task_details = self._task_details(task)

        return {
            "event": event,
            "host": result._host.get_name(),
            "play": self._current_play_name(),
            "task": task_details.get("name"),
            "module": task_details.get("action"),
            "path": task_details.get("path"),
            "line": task_details.get("line"),
            "item": result_data.get("item"),
            "message": self._first_result_text(result_data),
            "stdout": result_data.get("stdout"),
            "stderr": result_data.get("stderr"),
            "exception": result_data.get("exception"),
            "result": result_data,
        }

    @staticmethod
    def _first_result_text(result_data: Dict[str, Any]) -> Optional[str]:
        for key in ["msg", "stderr", "stdout", "exception"]:
            value = result_data.get(key)
            if value:
                return to_text(value)

        return None

    @staticmethod
    def _first_line(value: Any) -> str:
        lines = to_text(value).strip("\r\n").splitlines()
        return lines[0] if lines else ""

    @staticmethod
    def _recap_line(summary: Dict[str, Any]) -> str:
        keys = ["ok", "changed", "unreachable", "failures", "skipped", "rescued", "ignored"]
        return " ".join("%s=%s" % (key, int(summary.get(key, 0))) for key in keys)

    def _task_details(self, task: Any) -> Dict[str, Any]:
        if task is None:
            return {"name": "unknown", "action": "unknown", "path": None, "line": None}

        path = None
        line = None

        try:
            path = task.get_path()
        except Exception:
            path = None

        if path and ":" in path:
            path_parts = path.rsplit(":", 1)
            path = path_parts[0]
            try:
                line = int(path_parts[1])
            except ValueError:
                line = None

        return {
            "name": getattr(task, "name", None) or getattr(task, "action", "unknown"),
            "action": getattr(task, "action", "unknown"),
            "path": path,
            "line": line,
        }

    @staticmethod
    def _task_one_line(task: Optional[Dict[str, Any]]) -> str:
        if not task:
            return "unknown"

        value = "%s (%s)" % (task.get("name", "unknown"), task.get("action", "unknown"))

        if task.get("path"):
            value += " in %s" % task.get("path")

        if task.get("line"):
            value += ":%s" % task.get("line")

        return value

    @staticmethod
    def _play_name(play: Any) -> str:
        name = getattr(play, "name", None)
        return to_text(name) if name else "unnamed play"

    def _current_play_name(self) -> str:
        if self._play_names:
            return self._play_names[-1]

        return "unknown"

    @staticmethod
    def _hosts_from_play(play: Any) -> List[str]:
        try:
            hosts = play.hosts
        except Exception:
            return []

        if hosts is None:
            return []

        if isinstance(hosts, str):
            return [hosts]

        try:
            return [to_text(host) for host in hosts]
        except TypeError:
            return []

    def _remember_host_from_result(self, result: Any) -> None:
        self._remember_host(result._host.get_name())

    def _remember_host(self, host: str) -> None:
        if host and host not in self._target_hosts:
            self._target_hosts.append(host)

    def _hosts_with_count(self, stats: Any, key: str) -> List[str]:
        hosts = sorted(stats.processed.keys())
        return [host for host in hosts if int(stats.summarize(host).get(key, 0)) > 0]

    def _affected_hosts_for_status(self, status: str, stats: Any) -> List[str]:
        if status == "failure":
            return self._hosts_with_count(stats=stats, key="failures")

        if status == "unreachable":
            return self._hosts_with_count(stats=stats, key="unreachable")

        return sorted(stats.processed.keys())

    @staticmethod
    def _format_list(values: Iterable[str]) -> str:
        unique_values = sorted(set(value for value in values if value))
        return ", ".join(unique_values) if unique_values else "none"

    @staticmethod
    def _short_list(values: Iterable[str], limit: int) -> str:
        unique_values = sorted(set(value for value in values if value))
        if not unique_values:
            return "none"

        if len(unique_values) <= limit:
            return ",".join(unique_values)

        return "%s,+%s" % (",".join(unique_values[:limit]), len(unique_values) - limit)

    def _send_mail(self, sender: str, subject: str, body: str) -> None:
        sender_pair = email.utils.parseaddr(sender)
        sender_address = sender_pair[1]

        if not sender_address:
            self._display.warning("ebdruplab.automation.smtp_event: invalid sender address '%s'" % sender)
            return

        to_addresses = self._parse_addresses(self._get_str("to"))
        cc_addresses = self._parse_addresses(self._get_str("cc"))
        bcc_addresses = self._parse_addresses(self._get_str("bcc"))
        envelope_recipients = self._envelope_recipients([to_addresses, cc_addresses, bcc_addresses])

        if not envelope_recipients:
            self._display.warning("ebdruplab.automation.smtp_event: no valid recipient configured")
            return

        message = EmailMessage()
        message["Date"] = email.utils.formatdate(localtime=True)
        message["From"] = email.utils.formataddr(sender_pair)
        if to_addresses:
            message["To"] = self._format_addresses(to_addresses)
        if cc_addresses:
            message["Cc"] = self._format_addresses(cc_addresses)
        message["Message-ID"] = email.utils.make_msgid(domain=self._message_id_domain())
        message["Subject"] = to_text(subject).strip()
        message.set_content(to_text(body))

        try:
            smtp = self._connect_smtp()
            try:
                smtp.send_message(message, from_addr=sender_address, to_addrs=envelope_recipients)
                self._display.vvv("ebdruplab.automation.smtp_event: report mail sent successfully")
            finally:
                smtp.quit()

        except smtplib.SMTPException as exc:
            self._display.warning("ebdruplab.automation.smtp_event: SMTP error: %s" % exc)

        except socket.timeout:
            self._display.warning(
                "ebdruplab.automation.smtp_event: SMTP connection timed out after %s seconds"
                % self._get_int("timeout", default=30)
            )

        except OSError as exc:
            self._display.warning("ebdruplab.automation.smtp_event: SMTP connection failed: %s" % exc)

        except Exception as exc:
            self._display.warning("ebdruplab.automation.smtp_event: report mail failed: %s" % exc)

    def _connect_smtp(self) -> smtplib.SMTP:
        host = self._get_str("smtp_host") or "localhost"
        port = self._get_int("smtp_port", default=25)
        timeout = self._get_int("timeout", default=30)
        use_ssl = self._get_bool("use_ssl")
        starttls = self._get_bool("starttls")

        if starttls and use_ssl:
            raise ValueError("starttls and use_ssl cannot both be enabled")

        if use_ssl:
            smtp = smtplib.SMTP_SSL(
                host=host,
                port=port,
                timeout=timeout,
                context=self._tls_context(),
            )
        else:
            smtp = smtplib.SMTP(host=host, port=port, timeout=timeout)

        try:
            smtp.ehlo()

            if starttls:
                smtp.starttls(context=self._tls_context())
                smtp.ehlo()

            username = self._get_str("username")
            password = self._get_str("password")

            if username:
                smtp.login(username, password or "")

            return smtp

        except Exception:
            try:
                smtp.quit()
            except Exception:
                smtp.close()
            raise

    def _tls_context(self) -> ssl.SSLContext:
        if self._get_bool("validate_certs", default=True):
            return ssl.create_default_context()

        return ssl._create_unverified_context()

    def _message_id_domain(self) -> Optional[str]:
        configured = self._get_str("message_id_domain")
        return configured or socket.getfqdn()

    def _addresses_from_options(self, option_names: Iterable[str]) -> List[str]:
        recipients: List[str] = []

        for option_name in option_names:
            recipients.extend(
                self._envelope_recipients([self._parse_addresses(self._get_str(option_name))])
            )

        return recipients

    @staticmethod
    def _parse_addresses(value: Optional[str]) -> List[Tuple[str, str]]:
        if not value:
            return []

        return [address for address in email.utils.getaddresses([value]) if address[1]]

    @staticmethod
    def _format_addresses(addresses: Iterable[Tuple[str, str]]) -> str:
        return ", ".join(email.utils.formataddr(address) for address in addresses)

    @staticmethod
    def _envelope_recipients(address_groups: Iterable[Iterable[Tuple[str, str]]]) -> List[str]:
        recipients: List[str] = []

        for addresses in address_groups:
            for _name, address in addresses:
                if address:
                    recipients.append(address)

        return recipients

    @staticmethod
    def _indent(multiline: Any, indent: int = 8) -> str:
        return "\n".join((" " * indent) + line for line in to_text(multiline).splitlines())

    def _get_str(self, option_name: str) -> Optional[str]:
        value = self.get_option(option_name)

        if value is None:
            return None

        value = str(value).strip()

        if value == "":
            return None

        return value

    def _get_int(self, option_name: str, default: int) -> int:
        value = self.get_option(option_name)

        if value is None or str(value).strip() == "":
            return default

        try:
            return int(value)
        except ValueError:
            return default

    def _get_bool(self, option_name: str, default: bool = False) -> bool:
        value = self.get_option(option_name)

        if value is None:
            return default

        if isinstance(value, bool):
            return value

        return str(value).strip().lower() in {
            "1",
            "yes",
            "y",
            "true",
            "t",
            "on",
            "enabled",
        }
