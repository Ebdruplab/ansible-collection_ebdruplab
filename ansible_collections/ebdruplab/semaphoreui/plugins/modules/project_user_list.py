#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_user_list
short_description: List users linked to a Semaphore project
version_added: "2.0.0"
description:
  - Retrieves users linked to a specific project, with sortable and orderable results.
options:
  host:
    description: URL (with scheme) or IP of the Semaphore server.
    type: str
    required: true
  port:
    description: API port (e.g. 3000).
    type: int
    required: true
  project_id:
    description: Project ID to list users for.
    type: int
    required: true
  sort:
    description: Sort field.
    type: str
    choices: [name, username, email, role]
    default: name
  order:
    description: Sort order.
    type: str
    choices: [asc, desc]
    default: asc
  session_cookie:
    description: Session cookie for authentication.
    type: str
    required: false
    no_log: true
  api_token:
    description: API token for authentication.
    type: str
    required: false
    no_log: true
  validate_certs:
    description: Validate TLS certificates.
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: List project users (default sort by name asc)
  ebdruplab.semaphoreui.project_user_list:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1

- name: List project users sorted by email desc
  ebdruplab.semaphoreui.project_user_list:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 1
    sort: email
    order: desc
"""

RETURN = r"""
users:
  description: List of users linked to the project.
  type: list
  returned: success
status:
  description: HTTP status code.
  type: int
  returned: always
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            sort=dict(type="str", required=False, default="name", choices=["name", "username", "email", "role"]),
            order=dict(type="str", required=False, default="asc", choices=["asc", "desc"]),
            session_cookie=dict(type="str", required=False, no_log=True),
            api_token=dict(type="str", required=False, no_log=True),
            validate_certs=dict(type="bool", default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    sort = module.params["sort"]
    order = module.params["order"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/users?sort={sort}&order={order}"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers.setdefault("Accept", "application/json")

    try:
        body, status, _ = semaphore_get(
            url=url,
            headers=headers,
            validate_certs=validate_certs,
        )

        if status != 200:
            text = body.decode() if isinstance(body, (bytes, bytearray)) else str(body)
            module.fail_json(msg=f"Failed to list users: HTTP {status} - {text}", status=status)

        text = body.decode() if isinstance(body, (bytes, bytearray)) else body
        try:
            users = json.loads(text) if isinstance(text, str) and text else []
        except Exception:
            users = []

        module.exit_json(changed=False, users=users, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
