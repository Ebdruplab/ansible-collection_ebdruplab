#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r'''
---
module: project_task_delete
short_description: Delete a task from a Semaphore project
version_added: "1.0.0"
description:
  - Deletes a task (including its output) from the specified Semaphore project.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (e.g. http://localhost).
    type: str
    required: true
  port:
    description:
      - Port where Semaphore API is listening (e.g. 3000).
    type: int
    required: true
  session_cookie:
    description:
      - Session cookie for authentication (optional if api_token is used).
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - API token for authentication (optional if session_cookie is used).
    type: str
    required: false
    no_log: true
  project_id:
    description:
      - ID of the project the task belongs to.
    type: int
    required: true
  task_id:
    description:
      - ID of the task to delete.
    type: int
    required: true
  validate_certs:
    description:
      - Whether to validate TLS certificates.
    type: bool
    default: true
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Delete a task from a project
  ebdruplab.semaphoreui.project_task_delete:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    task_id: 8
'''

RETURN = r'''
msg:
  description:
    - A message indicating the result of the deletion operation.
  type: str
  returned: always
status:
  description:
    - HTTP status code returned by the Semaphore API.
  type: int
  returned: always
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            project_id=dict(type='int', required=True),
            task_id=dict(type='int', required=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    task_id = module.params["task_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/tasks/{task_id}"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        _, status, _ = semaphore_delete(
            url=url,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 204:
            module.fail_json(msg=f"DELETE failed with status {status}", status=status)

        module.exit_json(changed=True, msg="Task deleted successfully.", status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()

