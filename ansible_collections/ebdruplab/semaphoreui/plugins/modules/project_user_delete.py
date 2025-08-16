#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r"""
---
module: project_user_delete
short_description: Remove a user from a Semaphore project
version_added: "2.0.0"
description:
  - Unlinks (removes) a user from a specific Semaphore project.
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
  user_id:
    type: int
    required: true
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
- name: Remove user from project
  ebdruplab.semaphoreui.project_user_delete:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    user_id: 2
"""

RETURN = r"""
status:
  description: HTTP status code (204 on success).
  type: int
  returned: always
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            user_id=dict(type="int", required=True),
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
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/users/{user_id}"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )

    try:
        body, status, _ = semaphore_delete(url=url, headers=headers, validate_certs=validate_certs)

        if status != 204:
            text = body.decode() if isinstance(body, (bytes, bytearray)) else str(body)
            module.fail_json(msg=f"DELETE failed with status {status}: {text}", status=status)

        module.exit_json(changed=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
