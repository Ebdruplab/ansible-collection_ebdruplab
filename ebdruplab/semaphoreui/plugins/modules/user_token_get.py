#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: user_token_get
short_description: Fetch API tokens for the logged-in Semaphore user
version_added: "1.0.0"
description:
  - Retrieves the list of API tokens for the currently logged-in user.
options:
  host:
    type: str
    required: true
    description: Hostname of the Semaphore server (including protocol).
  port:
    type: int
    required: true
    description: Port of the Semaphore API (e.g. 3000).
  session_cookie:
    type: str
    required: false
    no_log: true
    description: Session cookie from login module.
  api_token:
    type: str
    required: false
    no_log: true
    description: API token for authentication.
  validate_certs:
    type: bool
    default: true
    description: Whether to validate TLS certificates.
author:
  - Kristian Ebdrup @kris9854
"""

EXAMPLES = r"""
- name: Get user API tokens
  ebdruplab.semaphoreui.user_token_get:
    host: http://localhost
    port: 3000
    api_token: "{{ login_result.api_token }}"
"""

RETURN = r"""
tokens:
  description: List of API tokens
  returned: always
  type: list
  elements: dict
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
    session_cookie = module.params.get("session_cookie")
    api_token = module.params.get("api_token")

    url = f"{host}:{port}/api/user/tokens"

    try:
        headers = get_auth_headers(session_cookie=session_cookie, api_token=api_token)
        headers["Content-Type"] = "application/json"

        response_body, status, _ = semaphore_get(
            url=url,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 200:
            error = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"Failed to fetch tokens: HTTP {status} - {error}", status=status)

        tokens = json.loads(response_body)
        module.exit_json(changed=False, tokens=tokens)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

