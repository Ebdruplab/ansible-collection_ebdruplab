#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers

DOCUMENTATION = r"""
---
module: logout
short_description: Logout of Semaphore UI
version_added: "1.0.0"
description:
  - Destroys the current session or invalidates the API token session in Semaphore.
options:
  host:
    description:
      - The URL or IP address of the Semaphore server.
    required: true
    type: str
  port:
    description:
      - The port on which the Semaphore UI is running.
    required: true
    type: int
  session_cookie:
    description:
      - Session cookie to invalidate.
    required: false
    type: str
    no_log: true
  api_token:
    description:
      - API token used for authentication.
    required: false
    type: str
    no_log: true
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
- name: Logout from Semaphore using session cookie
  ebdruplab.semaphoreui.logout:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"

- name: Logout from Semaphore using API token
  ebdruplab.semaphoreui.logout:
    host: http://localhost
    port: 3000
    api_token: "abcd1234"
"""

RETURN = r"""
changed:
  description: Whether the logout request was accepted.
  returned: always
  type: bool
  sample: true
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True)
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    validate_certs = module.params["validate_certs"]
    session_cookie = module.params.get("session_cookie")
    api_token = module.params.get("api_token")

    url = f"{host}:{port}/api/auth/logout"

    try:
        headers = get_auth_headers(
            session_cookie=session_cookie,
            api_token=api_token
        )

        _, status, _ = semaphore_post(
            url,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 204:
            module.fail_json(msg=f"Logout failed, status: {status}")

        module.exit_json(changed=True)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()

