#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r"""
---
module: user_delete
short_description: Delete a user in Semaphore
version_added: "1.0.0"
description:
  - Deletes a user by user ID in the Semaphore system.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (including protocol).
    type: str
    required: true
  port:
    description:
      - Port on which the Semaphore API is listening (e.g., 3000).
    type: int
    required: true
  user_id:
    description:
      - The ID of the user to delete.
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
      - API token used for authentication instead of session cookie.
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
- name: Delete a user by ID
  ebdruplab.semaphoreui.user_delete:
    host: http://localhost
    port: 3000
    user_id: 5
    session_cookie: "{{ login_result.session_cookie }}"
"""

RETURN = r"""
deleted:
  description: Whether the user was successfully deleted.
  type: bool
  returned: always
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            user_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    user_id = module.params["user_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/users/{user_id}"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        _, status, _ = semaphore_delete(
            url, headers=headers, validate_certs=validate_certs
        )

        if status != 204:
            module.fail_json(msg=f"Failed to delete user: HTTP {status}")

        module.exit_json(changed=True, deleted=True)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

