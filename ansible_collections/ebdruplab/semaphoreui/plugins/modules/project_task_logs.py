#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_task_logs
short_description: Retrieve logs for a Semaphore task
version_added: "1.0.0"
description:
  - Retrieves the output logs for a specific task in a Semaphore project.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server, including protocol.
    type: str
    required: true
  port:
    description:
      - Port where the Semaphore API is accessible.
    type: int
    required: true
  project_id:
    description:
      - ID of the project the task belongs to.
    type: int
    required: true
  task_id:
    description:
      - ID of the task whose logs to retrieve.
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
      - Bearer token for authentication.
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - Whether to validate TLS certificates.
    type: bool
    default: true
author:
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: Get logs for a task
  ebdruplab.semaphoreui.project_task_logs:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    task_id: 42
  register: task_logs

- name: Print log lines
  debug:
    var: task_logs.logs
'''

RETURN = r'''
logs:
  description: List of log entries for the task.
  type: list
  elements: dict
  returned: success
status:
  description: HTTP status code returned from the API.
  type: int
  returned: always
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            task_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True)
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    task_id = module.params["task_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/tasks/{task_id}/output"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        response_body, status, _ = semaphore_get(
            url=url,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 200:
            module.fail_json(msg=f"Failed to retrieve task logs: HTTP {status}", status=status)

        try:
            logs = json.loads(response_body)
            if not isinstance(logs, list):
                raise ValueError("Expected list of log entries")
        except Exception as e:
            module.fail_json(msg=f"Failed to parse logs: {e}", raw=response_body)

        module.exit_json(changed=False, logs=logs, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

