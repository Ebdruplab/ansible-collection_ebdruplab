#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_integration_matcher_get
short_description: List matchers for a Semaphore integration
version_added: "2.0.0"
description:
  - Retrieves all matcher rules linked to a given integration in a Semaphore project.

options:
  host:
    description:
      - Base URL of the Semaphore server including scheme (e.g. C(http://localhost)).
    type: str
    required: true
  port:
    description:
      - Port where the Semaphore API is exposed (e.g. C(3000)).
    type: int
    required: true
  project_id:
    description:
      - ID of the project that owns the integration.
    type: int
    required: true
  integration_id:
    description:
      - ID of the integration whose matchers should be listed.
    type: int
    required: true
  session_cookie:
    description:
      - Session cookie for authentication. Use this or C(api_token).
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - Bearer token for authentication. Use this or C(session_cookie).
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - Whether to validate TLS certificates when using HTTPS.
    type: bool
    default: true

author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Get matchers for an integration
  ebdruplab.semaphoreui.project_integration_matcher_get:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 1
    integration_id: 11
  register: matcher_result

- name: Show matcher count
  ansible.builtin.debug:
    msg: "Found {{ matcher_result.matchers | length }} matcher(s)."
"""

RETURN = r"""
matchers:
  description:
    - List of matcher objects returned by the API.
  type: list
  returned: success
status:
  description:
    - HTTP status code (200 on success).
  type: int
  returned: always
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            integration_id=dict(type="int", required=True),
            session_cookie=dict(type="str", required=False, no_log=True),
            api_token=dict(type="str", required=False, no_log=True),
            validate_certs=dict(type="bool", default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    integration_id = module.params["integration_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/integrations/{integration_id}/matchers"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers.setdefault("Accept", "application/json")

    try:
        response_body, status, _ = semaphore_get(
            url=url, headers=headers, validate_certs=validate_certs
        )

        if status != 200:
            text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else str(response_body)
            module.fail_json(msg=f"GET failed with status {status}: {text}", status=status)

        text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else response_body
        try:
            matchers = json.loads(text) if isinstance(text, str) else text
        except Exception:
            matchers = {"raw": text}

        module.exit_json(changed=False, matchers=matchers, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
