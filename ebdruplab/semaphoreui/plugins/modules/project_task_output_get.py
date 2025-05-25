#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_task_output_get
short_description: Get output logs for a Semaphore task
version_added: "1.0.0"
description:
  - Retrieves the output lines of a specific task in a Semaphore project.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server, including protocol.
    type: str
    required: true
  port:
    description:
      - Port number where Semaphore API is accessible.
    type: int
    required: true
  session_cookie:
    description:
      - Authentication session cookie.
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - API token for authentication.
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
      - ID of the task whose output to retrieve.
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
- name: Get task output logs
  ebdruplab.semaphoreui.project_task_output_get:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    task_id: 23
  register: task_output

- name: Display output lines
  debug:
    var: task_output.output
'''

RETURN = r'''
output:
  description: List of output lines for the specified task.
  type: list
  elements: dict
  returned: success
  sample:
    - task_id: 23
      time: "2025-04-24T19:29:26.672Z"
      output: "Started playbook execution"
status:
  description: HTTP response code from the API.
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

    url = f"{host}:{port}/api/project/{project_id}/tasks/{task_id}/output"
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
            module.fail_json(msg=f"Failed to retrieve task output: HTTP {status}", status=status)

        try:
            output_lines = json.loads(response_body)
            if not isinstance(output_lines, list):
                raise ValueError("Expected a list of output lines")
        except Exception as e:
            module.fail_json(msg=f"Failed to parse response: {e}", raw=response_body)

        module.exit_json(changed=False, output=output_lines, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()

