#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post
import json

DOCUMENTATION = r"""
---
module: login
short_description: Log into Semaphore UI
version_added: "1.0.0"
description:
  - Logs into the Semaphore UI and returns a session cookie used for authenticated requests.
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
  username:
    description:
      - Username for logging in.
    required: true
    type: str
  password:
    description:
      - Password for the user.
    required: true
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
- name: Log in to Semaphore
  ebdruplab.semaphoreui.login:
    host: http://localhost
    port: 3000
    username: admin
    password: changeme
  register: login_result

- name: Use session cookie
  debug:
    msg: "Authenticated with cookie {{ login_result.session_cookie }}"
"""

RETURN = r"""
session_cookie:
  description: The session cookie used for further authenticated requests.
  returned: success
  type: str
  sample: "semaphore_session=abc123xyz;"
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            username=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        supports_check_mode=False
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    username = module.params["username"]
    password = module.params["password"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/auth/login"
    payload = {
        "auth": username,
        "password": password
    }

    try:
        _, status, cookie = semaphore_post(url, body=payload, validate_certs=validate_certs)
        if status != 204:
            module.fail_json(msg=f"Login failed, status: {status}")
        module.exit_json(changed=False, session_cookie=cookie)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()

