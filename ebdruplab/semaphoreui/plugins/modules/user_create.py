#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: user_create
short_description: Create a new user in Semaphore
version_added: "1.0.0"
description:
  - Creates a user with specified attributes in the Semaphore system.
  - Requires admin permissions.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (including protocol).
    type: str
    required: true
  port:
    description:
      - Port on which the Semaphore API is listening.
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
  name:
    description:
      - Full name of the user.
    type: str
    required: true
  username:
    description:
      - Username used to log in.
    type: str
    required: true
  email:
    description:
      - Email address of the user.
    type: str
    required: true
  password:
    description:
      - Password for the user.
    type: str
    required: true
    no_log: true
  alert:
    description:
      - Whether to send alerts to the user.
    type: bool
    default: false
  admin:
    description:
      - Whether the user has admin privileges.
    type: bool
    default: false
  external:
    description:
      - Whether the user is managed externally (e.g. LDAP).
    type: bool
    default: false
  validate_certs:
    description:
      - Whether to validate TLS certificates.
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Create a new user
  ebdruplab.semaphoreui.user_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    name: "Jane Smith"
    username: "jsmith"
    email: "jane@example.com"
    password: "supersecure123"
    admin: true
    alert: true
"""

RETURN = r"""
user:
  description: The created user object.
  type: dict
  returned: success
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            name=dict(type='str', required=True),
            username=dict(type='str', required=True),
            email=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            alert=dict(type='bool', default=False),
            admin=dict(type='bool', default=False),
            external=dict(type='bool', default=False),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
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

    payload = {
        "name": module.params["name"],
        "username": module.params["username"],
        "email": module.params["email"],
        "password": module.params["password"],
        "alert": module.params["alert"],
        "admin": module.params["admin"],
        "external": module.params["external"],
    }

    try:
        body = json.dumps(payload).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url, body=body, headers=headers, validate_certs=validate_certs
        )

        if status != 201:
            module.fail_json(msg=f"POST failed with status {status}: {response_body}")

        user = json.loads(response_body)
        module.exit_json(changed=True, user=user)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

