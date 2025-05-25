#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: user_update
short_description: Update a Semaphore user
version_added: "1.0.0"
description:
  - Updates user information including name, username, email, alert flag, and admin privileges.
options:
  host:
    type: str
    required: true
    description: Hostname of the Semaphore server (including protocol).
  port:
    type: int
    required: true
    description: Port on which Semaphore API is accessible.
  user_id:
    type: int
    required: true
    description: ID of the user to update.
  name:
    type: str
    required: true
    description: Full name of the user.
  username:
    type: str
    required: true
    description: Username for login.
  email:
    type: str
    required: true
    description: User's email address.
  alert:
    type: bool
    default: false
    description: Whether the user should receive alerts.
  admin:
    type: bool
    default: false
    description: Whether the user has admin privileges.
  session_cookie:
    type: str
    required: false
    no_log: true
    description: Session cookie for authentication.
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
'''

EXAMPLES = r'''
- name: Update user details
  ebdruplab.semaphoreui.user_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    user_id: 5
    name: "Jane Doe"
    username: "jane"
    email: "jane@example.com"
    alert: true
    admin: false
'''

RETURN = r'''
updated:
  description: Whether the user was successfully updated.
  type: bool
  returned: always
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            user_id=dict(type='int', required=True),
            name=dict(type='str', required=True),
            username=dict(type='str', required=True),
            email=dict(type='str', required=True),
            alert=dict(type='bool', default=False),
            admin=dict(type='bool', default=False),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
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

    payload = {
        "name": module.params["name"],
        "username": module.params["username"],
        "email": module.params["email"],
        "alert": module.params["alert"],
        "admin": module.params["admin"],
    }

    try:
        body = json.dumps(payload).encode("utf-8")
        _, status, _ = semaphore_put(
            url=url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 204:
            module.fail_json(msg=f"Failed to update user: HTTP {status}", status=status)

        module.exit_json(changed=True, updated=True)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

