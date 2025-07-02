#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: user_token_create
short_description: Create an API token for the logged-in user
version_added: "1.0.0"
description:
  - Sends a POST request to create a new API token for the currently authenticated user in Semaphore.
options:
  host:
    description:
      - Full hostname or IP of the Semaphore server (e.g., http://localhost).
    type: str
    required: true
  port:
    description:
      - Port on which the Semaphore API is available.
    type: int
    required: true
  session_cookie:
    description:
      - Session cookie used for authentication.
    type: str
    required: true
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
- name: Create API token
  ebdruplab.semaphoreui.user_token_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
"""

RETURN = r"""
token:
  description: The created API token object.
  returned: success
  type: dict
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=True, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        supports_check_mode=False
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    validate_certs = module.params["validate_certs"]
    session_cookie = module.params["session_cookie"]

    url = f"{host}:{port}/api/user/tokens"

    headers = get_auth_headers(session_cookie=session_cookie)
    headers["Content-Type"] = "application/json"

    try:
        response_body, status, _ = semaphore_post(
            url,
            body=None,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 201:
            module.fail_json(msg=f"Failed to create token: HTTP {status}", response=response_body)

        token = json.loads(response_body)
        module.exit_json(changed=True, token=token)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

