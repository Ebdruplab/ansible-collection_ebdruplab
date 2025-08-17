#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_user_create
short_description: Link a user to a Semaphore project with a role
version_added: "2.0.0"
description:
  - Adds an existing user to a project with a specific role.
  - Accepted roles (as in the UI): C(Owner), C(Manager), C(Task Runner), C(Guest).
  - Input is case-insensitive; C(Task Runner) may be written as "task runner", "task_runner", or "task-runner".
options:
  host:
    type: str
    required: true
  port:
    type: int
    required: true
  project_id:
    type: int
    required: true
  user:
    description: User and role to add to the project.
    type: dict
    required: true
    suboptions:
      user_id:
        type: int
        required: true
      role:
        type: str
        required: true
        description:
          - One of C(Owner), C(Manager), C(task_runner), C(Guest).
  session_cookie:
    type: str
    required: false
    no_log: true
  api_token:
    type: str
    required: false
    no_log: true
  validate_certs:
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Add user as Owner
  ebdruplab.semaphoreui.project_user_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    user:
      user_id: 42
      role: Owner

- name: Add user as Task Runner (flexible separators/case)
  ebdruplab.semaphoreui.project_user_create:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 1
    user:
      user_id: 99
      role: task_runner
"""

RETURN = r"""
status:
  description: HTTP status (204 on success).
  type: int
  returned: always
user:
  description: Echo of the assignment (returned when server sends no body).
  type: dict
  returned: when status is 204
"""

def _normalize_role(module, role):
    """
    Normalize UI roles to API values: owner | manager | task-runner | guest.
    Accepts case-insensitive and -, _, or space for 'Task Runner'.
    """
    if not isinstance(role, str) or not role.strip():
        module.fail_json(msg="user.role must be a non-empty string.")

    v = role.strip().lower().replace("_", " ").replace("-", " ")
    if v == "owner":
        return "owner"
    if v == "manager":
        return "manager"
    if v in ("task runner", "taskrunner","task_runner"):
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
            user=dict(
                type="dict",
                required=True,
                options=dict(
                    user_id=dict(type="int", required=True),
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
    user = module.params["user"] or {}
    user_id = user.get("user_id")
    role = _normalize_role(module, user.get("role"))

    url = f"{host}:{port}/api/project/{project_id}/users"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers["Content-Type"] = "application/json"
    headers.setdefault("Accept", "application/json")

    payload = {"user_id": int(user_id), "role": role}

    try:
        body = json.dumps(payload).encode("utf-8")
        resp_body, status, _ = semaphore_post(
            url=url, body=body, headers=headers, validate_certs=module.params["validate_certs"]
        )

        if status == 204:
            module.exit_json(changed=True, status=status, user=dict(payload, project_id=project_id))

        if status in (200, 201):
            text = resp_body.decode() if isinstance(resp_body, (bytes, bytearray)) else resp_body
            try:
                obj = json.loads(text) if isinstance(text, str) else text
            except Exception:
                obj = {"raw": text}
            module.exit_json(changed=True, status=status, user=obj)

        text = resp_body.decode() if isinstance(resp_body, (bytes, bytearray)) else str(resp_body)
        module.fail_json(msg=f"POST failed with status {status}: {text}", status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
