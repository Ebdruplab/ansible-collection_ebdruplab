#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: events
short_description: Get events from Semaphore
version_added: "1.0.0"
description:
  - Retrieves events related to Semaphore and projects accessible to the user.
options:
  host:
    description:
      - The URL or IP address of the Semaphore server.
    required: true
    type: str
  port:
    description:
      - The port on which the Semaphore API is running.
    required: true
    type: int
  session_cookie:
    description:
      - Session cookie used for authentication.
    required: false
    type: str
    no_log: true
  api_token:
    description:
      - API token used for authentication.
    required: false
    type: str
    no_log: true
  last_only:
    description:
      - Whether to only fetch the last 200 events.
    required: false
    type: bool
    default: false
  validate_certs:
    description:
      - Whether to validate TLS certificates.
    required: false
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Fetch all events
  ebdruplab.semaphoreui.events:
    host: http://localhost
    port: 3000
    api_token: "abcd1234"

- name: Fetch last 200 events
  ebdruplab.semaphoreui.events:
    host: http://localhost
    port: 3000
    api_token: "abcd1234"
    last_only: true
"""

RETURN = r"""
events:
  description: List of events retrieved from Semaphore.
  returned: success
  type: list
  elements: dict
  sample:
    - id: 12
      type: task_finished
      project_id: 1
      message: Task completed
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            last_only=dict(type='bool', default=False),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    validate_certs = module.params["validate_certs"]
    last_only = module.params["last_only"]

    endpoint = "/events/last" if last_only else "/api/events"
    url = f"{host}:{port}{endpoint}"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        response_body, status, _ = semaphore_get(
            url, headers=headers, validate_certs=validate_certs
        )

        if status != 200:
            module.fail_json(msg=f"Failed to fetch events: HTTP {status}", response=response_body)

        try:
            events = json.loads(response_body) if response_body else []
        except json.JSONDecodeError:
            module.fail_json(msg="Invalid JSON response", raw=response_body)

        module.exit_json(changed=False, events=events)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

