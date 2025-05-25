#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_task_get
short_description: Get a single task in a Semaphore project
version_added: "1.0.0"
description:
  - Retrieves details of a specific task in a project by ID.
options:
  host:
    description:
      - Hostname or IP (including protocol) of the Semaphore server.
    type: str
    required: true
  port:
    description:
      - Port where the Semaphore API is listening (e.g., 3000).
    type: int
    required: true
  session_cookie:
    description:
      - Session cookie from login.
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - Bearer token for authentication.
    type: str
    required: false
    no_log: true
  project_id:
    description:
      - ID of the project that contains the task.
    type: int
    required: true
  task_id:
    description:
      - ID of the task to retrieve.
    type: int
    required: true
  validate_certs:
    description:
      - Whether to validate TLS certificates.
    type: bool
    default: true
author:
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: Get details of a specific task
  ebdruplab.semaphoreui.project_task_get:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    task_id: 23
  register: task_info

- name: Display task
  debug:
    var: task_info.task
'''

RETURN = r'''
task:
  description: Task detail object.
  type: dict
  returned: success
status:
  description: HTTP status code from the Semaphore API.
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
        supports_check_mode=True,
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
        response_body, status, _ = semaphore_get(
            url=url, headers=headers, validate_certs=validate_certs
        )

        if status != 200:
            module.fail_json(msg=f"Failed to fetch task: HTTP {status}", status=status, response=response_body)

        task = json.loads(response_body)
        module.exit_json(changed=False, task=task, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()

