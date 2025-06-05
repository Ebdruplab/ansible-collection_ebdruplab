#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: user_password_update
short_description: Update a user's password in Semaphore
version_added: "1.0.0"
description:
  - Updates the password for a specific Semaphore user.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (including protocol).
    type: str
    required: true
  port:
    description:
      - Port number where the Semaphore API is running.
    type: int
    required: true
  user_id:
    description:
      - ID of the user whose password will be updated.
    type: int
    required: true
  password:
    description:
      - New password for the user.
    type: str
    required: true
    no_log: true
  session_cookie:
    description:
      - Authentication session cookie.
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
- name: Update user password
  ebdruplab.semaphoreui.user_password_update:
    host: http://localhost
    port: 3000
    user_id: 2
    session_cookie: "{{ login_result.session_cookie }}"
    password: "newpassword123"
"""

RETURN = r"""
status:
  description: HTTP status code of the update response
  type: int
  returned: always
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            user_id=dict(type='int', required=True),
            password=dict(type='str', required=True, no_log=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    user_id = module.params["user_id"]
    validate_certs = module.params["validate_certs"]
    password = module.params["password"]

    url = f"{host}:{port}/api/users/{user_id}/password"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    payload = {"password": password}

    try:
        body = json.dumps(payload).encode("utf-8")
        _, status, _ = semaphore_post(
            url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 204:
            module.fail_json(msg=f"Failed to update password: HTTP {status}", status=status)

        module.exit_json(changed=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

