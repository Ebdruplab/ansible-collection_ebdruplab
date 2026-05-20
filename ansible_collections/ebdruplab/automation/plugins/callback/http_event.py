# -*- coding: utf-8 -*-
# Copyright (c) 2026, Kristian Ebdrup
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
name: http_event
short_description: Send Ansible playbook result events to HTTP endpoints
description:
  - Sends an HTTP request when an Ansible playbook finishes.
  - Supports separate URLs for success, failure, and unreachable results.
  - Supports token authentication, status headers, custom headers, and host headers.
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
      - section: callback_http_event
        key: enabled
    env:
      - name: EBDRUPLAB_AUTOMATION_HTTP_EVENT_ENABLED

  success_url:
    description:
      - HTTP endpoint called when the playbook completes successfully.
    type: str
    required: false
    ini:
      - section: callback_http_event
        key: success_url
    env:
      - name: EBDRUPLAB_AUTOMATION_HTTP_EVENT_SUCCESS_URL

  failure_url:
    description:
      - HTTP endpoint called when one or more hosts fail.
    type: str
    required: false
    ini:
      - section: callback_http_event
        key: failure_url
    env:
      - name: EBDRUPLAB_AUTOMATION_HTTP_EVENT_FAILURE_URL

  unreachable_url:
    description:
      - HTTP endpoint called when one or more hosts are unreachable.
    type: str
    required: false
    ini:
      - section: callback_http_event
        key: unreachable_url
    env:
      - name: EBDRUPLAB_AUTOMATION_HTTP_EVENT_UNREACHABLE_URL

  auth_token:
    description:
      - Authentication token value added to the configured authentication header.
      - No authentication header is sent when this value is empty.
    type: str
    required: false
    ini:
      - section: callback_http_event
        key: auth_token
    env:
      - name: EBDRUPLAB_AUTOMATION_HTTP_EVENT_AUTH_TOKEN

  auth_header:
    description:
      - Header key used for authentication.
    type: str
    default: Authorization
    ini:
      - section: callback_http_event
        key: auth_header
    env:
      - name: EBDRUPLAB_AUTOMATION_HTTP_EVENT_AUTH_HEADER

  auth_scheme:
    description:
      - Authentication scheme prepended to the token.
      - Use an empty value to send the raw token.
    type: str
    default: Bearer
    ini:
      - section: callback_http_event
        key: auth_scheme
    env:
      - name: EBDRUPLAB_AUTOMATION_HTTP_EVENT_AUTH_SCHEME

  status_header:
    description:
      - Header key containing the final Ansible job status.
      - The value is one of C(success), C(failure), or C(unreachable).
    type: str
    default: X-Ansible-Job-Status
    ini:
      - section: callback_http_event
        key: status_header
    env:
      - name: EBDRUPLAB_AUTOMATION_HTTP_EVENT_STATUS_HEADER

  extra_headers:
    description:
      - Additional static headers.
      - Format is comma-separated key/value pairs.
      - 'Example: C(X-Source=ansible,X-Environment=production).'
    type: str
    required: false
    ini:
      - section: callback_http_event
        key: extra_headers
    env:
      - name: EBDRUPLAB_AUTOMATION_HTTP_EVENT_EXTRA_HEADERS

  host_header:
    description:
      - Optional header key containing affected host names.
      - The value is a comma-separated list of hosts relevant to the final status.
    type: str
    required: false
    ini:
      - section: callback_http_event
        key: host_header
    env:
      - name: EBDRUPLAB_AUTOMATION_HTTP_EVENT_HOST_HEADER

  timeout:
    description:
      - HTTP request timeout in seconds.
    type: int
    default: 10
    ini:
      - section: callback_http_event
        key: timeout
    env:
      - name: EBDRUPLAB_AUTOMATION_HTTP_EVENT_TIMEOUT

  validate_certs:
    description:
      - Validate TLS certificates when using HTTPS.
    type: bool
    default: true
    ini:
      - section: callback_http_event
        key: validate_certs
    env:
      - name: EBDRUPLAB_AUTOMATION_HTTP_EVENT_VALIDATE_CERTS

  method:
    description:
      - HTTP method used for callback requests.
    type: str
    default: POST
    choices:
      - POST
      - PUT
      - PATCH
    ini:
      - section: callback_http_event
        key: method
    env:
      - name: EBDRUPLAB_AUTOMATION_HTTP_EVENT_METHOD

  send_body:
    description:
      - Send a JSON request body with playbook result details.
    type: bool
    default: true
    ini:
      - section: callback_http_event
        key: send_body
    env:
      - name: EBDRUPLAB_AUTOMATION_HTTP_EVENT_SEND_BODY
"""

import json
import socket
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from urllib.error import HTTPError
from urllib.error import URLError

from ansible.module_utils.urls import open_url
from ansible.plugins.callback import CallbackBase

CALLBACK_VERSION = 2.0
CALLBACK_TYPE = "aggregate"
CALLBACK_NAME = "ebdruplab.automation.http_event"
CALLBACK_NEEDS_ENABLED = True


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = CALLBACK_VERSION
    CALLBACK_TYPE = CALLBACK_TYPE
    CALLBACK_NAME = CALLBACK_NAME
    CALLBACK_NEEDS_ENABLED = CALLBACK_NEEDS_ENABLED

    def __init__(self) -> None:
        super().__init__()
        self._options_loaded = False

    def set_options(
        self,
        task_keys: Optional[Dict[str, Any]] = None,
        var_options: Optional[Dict[str, Any]] = None,
        direct: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().set_options(task_keys=task_keys, var_options=var_options, direct=direct)
        self._options_loaded = True

    def v2_playbook_on_stats(self, stats: Any) -> None:
        self._ensure_options_loaded()

        if not self._get_bool("enabled"):
            return

        status = self._determine_status(stats)
        url = self._url_for_status(status)

        if not url:
            self._display.vvv(
                "ebdruplab.automation.http_event: no URL configured for status '%s'" % status
            )
            return

        affected_hosts = self._affected_hosts_for_status(status, stats)
        headers = self._build_headers(status=status, hosts=affected_hosts)
        body = self._build_body(status=status, hosts=affected_hosts, stats=stats)

        self._send_request(url=url, headers=headers, body=body)

    def _ensure_options_loaded(self) -> None:
        if not self._options_loaded:
            try:
                self.set_options()
            except Exception:
                pass

    def _determine_status(self, stats: Any) -> str:
        hosts = sorted(stats.processed.keys())

        failed_hosts = [
            host
            for host in hosts
            if int(stats.summarize(host).get("failures", 0)) > 0
        ]

        unreachable_hosts = [
            host
            for host in hosts
            if int(stats.summarize(host).get("unreachable", 0)) > 0
        ]

        if failed_hosts:
            return "failure"

        if unreachable_hosts:
            return "unreachable"

        return "success"

    def _url_for_status(self, status: str) -> Optional[str]:
        urls = {
            "success": self._get_str("success_url"),
            "failure": self._get_str("failure_url"),
            "unreachable": self._get_str("unreachable_url"),
        }

        return urls.get(status)

    def _affected_hosts_for_status(self, status: str, stats: Any) -> List[str]:
        hosts = sorted(stats.processed.keys())

        if status == "failure":
            return [
                host
                for host in hosts
                if int(stats.summarize(host).get("failures", 0)) > 0
            ]

        if status == "unreachable":
            return [
                host
                for host in hosts
                if int(stats.summarize(host).get("unreachable", 0)) > 0
            ]

        return hosts

    def _build_headers(self, status: str, hosts: Iterable[str]) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": "ebdruplab.automation.http_event",
        }

        auth_token = self._get_str("auth_token")
        auth_header = self._get_str("auth_header") or "Authorization"
        auth_scheme = self._get_str("auth_scheme")

        if auth_token:
            if auth_scheme:
                headers[auth_header] = "%s %s" % (auth_scheme, auth_token)
            else:
                headers[auth_header] = auth_token

        status_header = self._get_str("status_header") or "X-Ansible-Job-Status"
        if status_header:
            headers[status_header] = status

        host_header = self._get_str("host_header")
        if host_header:
            headers[host_header] = ",".join(sorted(set(hosts)))

        headers.update(self._parse_extra_headers(self._get_str("extra_headers")))

        return headers

    def _build_body(self, status: str, hosts: List[str], stats: Any) -> Optional[bytes]:
        if not self._get_bool("send_body", default=True):
            return None

        all_hosts = sorted(stats.processed.keys())

        payload = {
            "status": status,
            "hosts": hosts,
            "summary": {
                host: stats.summarize(host)
                for host in all_hosts
            },
            "failed_hosts": [
                host
                for host in all_hosts
                if int(stats.summarize(host).get("failures", 0)) > 0
            ],
            "unreachable_hosts": [
                host
                for host in all_hosts
                if int(stats.summarize(host).get("unreachable", 0)) > 0
            ],
            "ok_hosts": [
                host
                for host in all_hosts
                if int(stats.summarize(host).get("ok", 0)) > 0
            ],
            "changed_hosts": [
                host
                for host in all_hosts
                if int(stats.summarize(host).get("changed", 0)) > 0
            ],
        }

        return json.dumps(payload, sort_keys=True).encode("utf-8")

    def _send_request(
        self,
        url: str,
        headers: Dict[str, str],
        body: Optional[bytes],
    ) -> None:
        method = (self._get_str("method") or "POST").upper()
        timeout = self._get_int("timeout", default=10)
        validate_certs = self._get_bool("validate_certs", default=True)

        try:
            with open_url(
                url,
                data=body,
                headers=headers,
                method=method,
                timeout=timeout,
                validate_certs=validate_certs,
            ) as response:
                response.read()
                self._display.vvv(
                    "ebdruplab.automation.http_event: callback sent successfully, status_code=%s"
                    % getattr(response, "status", "unknown")
                )

        except HTTPError as exc:
            self._display.warning(
                "ebdruplab.automation.http_event: callback failed with HTTP status %s"
                % exc.code
            )

        except URLError as exc:
            self._display.warning(
                "ebdruplab.automation.http_event: callback failed: %s"
                % exc.reason
            )

        except socket.timeout:
            self._display.warning(
                "ebdruplab.automation.http_event: callback timed out after %s seconds"
                % timeout
            )

        except Exception as exc:
            self._display.warning(
                "ebdruplab.automation.http_event: callback failed: %s"
                % exc
            )

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

    @staticmethod
    def _parse_extra_headers(value: Optional[str]) -> Dict[str, str]:
        headers: Dict[str, str] = {}

        if not value:
            return headers

        for item in value.split(","):
            item = item.strip()

            if not item or "=" not in item:
                continue

            key, header_value = item.split("=", 1)
            key = key.strip()
            header_value = header_value.strip()

            if key:
                headers[key] = header_value

        return headers
