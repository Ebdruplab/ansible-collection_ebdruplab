#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_task_list
short_description: List tasks in a Semaphore project
version_added: "1.0.0"
description:
  - Retrieves a list of all tasks related to the given project in chronological order.
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
      - Session authentication cookie.
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
      - ID of the Semaphore project whose tasks to list.
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
- name: List all tasks in a project
  ebdruplab.semaphoreui.project_task_list:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
  register: task_list

- name: Show task IDs
  debug:
    var: task_list.tasks | map(attribute='id') | list
'''

RETURN = r'''
tasks:
  description: List of tasks for the project.
  type: list
  elements: dict
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
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/tasks"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        response_body, status, _ = semaphore_get(
            url, headers=headers, validate_certs=validate_certs
        )

        if status != 200:
            module.fail_json(msg=f"Failed to list tasks: HTTP {status}", status=status, response=response_body)

        try:
            tasks = json.loads(response_body)
            if not isinstance(tasks, list):
                raise ValueError("Expected list")
        except Exception as e:
            module.fail_json(msg=f"Invalid response format: {str(e)}", raw=response_body)

        module.exit_json(changed=False, tasks=tasks, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()

