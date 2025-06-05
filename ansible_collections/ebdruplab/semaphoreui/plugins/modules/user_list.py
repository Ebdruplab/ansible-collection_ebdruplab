#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: user_list
short_description: List all users in Semaphore
version_added: "1.0.0"
description:
  - Retrieves a list of all users in the Semaphore instance.
  - Requires admin permissions to access the full list.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (including protocol).
    type: str
    required: true
  port:
    description:
      - Port where the Semaphore API is accessible (e.g., 3000).
    type: int
    required: true
  session_cookie:
    description:
      - Session cookie used for authentication.
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - API token for authentication.
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - Whether to validate TLS certificates.
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: List all users
  ebdruplab.semaphoreui.user_list:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
"""

RETURN = r"""
users:
  description: A list of users in the Semaphore system.
  type: list
  elements: dict
  returned: success
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/users"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        body, status, _ = semaphore_get(url, headers=headers, validate_certs=validate_certs)

        if status != 200:
            module.fail_json(msg=f"Failed to list users: HTTP {status}", response=body)

        users = json.loads(body)
        module.exit_json(changed=False, users=users)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

