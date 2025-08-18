#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_user_update
short_description: Update a user's role in a Semaphore project
version_added: "2.0.0"
description:
  - Sets the role for an existing user linked to a project. Role input is case-insensitive and accepts common separators.
options:
  host:
    description: Base URL of the Semaphore server including scheme, for example http://localhost.
    type: str
    required: true
  port:
    description: Port where the Semaphore API is exposed, for example 3000.
    type: int
    required: true
  project_id:
    description: ID of the project that the user is linked to.
    type: int
    required: true
  user_id:
    description: ID of the user whose role will be updated.
    type: int
    required: true
  user:
    description: Payload containing the new role.
    type: dict
    required: true
    suboptions:
      role:
        description: Project role for the user. One of "Owner", "Manager", "Task Runner", or "Guest".
        type: str
        required: true
  session_cookie:
    description: Session cookie for authentication. Use this or api_token.
    type: str
    required: false
    no_log: true
  api_token:
    description: API token for authentication. Use this or session_cookie.
    type: str
    required: false
    no_log: true
  validate_certs:
    description: Validate TLS certificates when using HTTPS.
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Set user role to Owner
  ebdruplab.semaphoreui.project_user_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    user_id: 2
    user:
      role: "Owner"

- name: Set user role to Task Runner (any separator/case accepted)
  ebdruplab.semaphoreui.project_user_update:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 1
    user_id: 2
    user:
      role: "task_runner"
"""

RETURN = r"""
status:
  description: HTTP status code (204 on success).
  type: int
  returned: always
changed:
  description: Whether an update occurred.
  type: bool
  returned: always
"""

def _normalize_role(module, role):
    """
    Accept UI role labels (Owner, Manager, Task Runner, Guest) in any case.
    Normalize to API values: owner | manager | task_runner | guest.
    Also accept "task_runner", "task runner", "taskrunner".
    """
    if not isinstance(role, str) or not role.strip():
        module.fail_json(msg="user.role must be a non-empty string.")

    v = role.strip().lower().replace("_", " ").replace("-", " ")
    if v == "owner":
        return "owner"
    if v == "manager":
        return "manager"
    if v in ("task runner", "taskrunner"):
        return "task_runner"
    if v == "guest":
        return "guest"

    module.fail_json(msg="Invalid role '%s'. Allowed: Owner, Manager, Task Runner, Guest." % role)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            user_id=dict(type="int", required=True),
            user=dict(
                type="dict",
                required=True,
                options=dict(
                    role=dict(type="str", required=True),
                ),
            ),
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
    user_id = module.params["user_id"]
    raw_role = (module.params["user"] or {}).get("role")

    role = _normalize_role(module, raw_role)

    url = f"{host}:{port}/api/project/{project_id}/users/{user_id}"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers["Content-Type"] = "application/json"
    headers.setdefault("Accept", "application/json")

    try:
        body = json.dumps({"role": role}).encode("utf-8")
        resp_body, status, _ = semaphore_put(
            url=url, body=body, headers=headers, validate_certs=module.params["validate_certs"]
        )

        if status != 204:
            text = resp_body.decode() if isinstance(resp_body, (bytes, bytearray)) else str(resp_body)
            module.fail_json(msg=f"PUT failed with status {status}: {text}", status=status)

        module.exit_json(changed=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
