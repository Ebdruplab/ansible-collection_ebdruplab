#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers

DOCUMENTATION = r'''
---
module: project_task_raw_output
short_description: Get raw output of a task in Semaphore
version_added: "1.0.0"
description:
  - Retrieves the raw output from a specific task in a Semaphore project.
options:
  host:
    type: str
    required: true
    description: Hostname of the Semaphore server, including protocol (e.g., http://localhost).
  port:
    type: int
    required: true
    description: Port of the Semaphore server (e.g., 3000).
  project_id:
    type: int
    required: true
    description: ID of the project containing the task.
  task_id:
    type: int
    required: true
    description: ID of the task to get the raw output from.
  session_cookie:
    type: str
    required: false
    no_log: true
    description: Session cookie from a previous login.
  api_token:
    type: str
    required: false
    no_log: true
    description: API token to authenticate instead of session cookie.
  validate_certs:
    type: bool
    default: true
    description: Whether to validate TLS certificates.
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Get raw output from task 8
  ebdruplab.semaphoreui.project_task_raw_output:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    task_id: 8
'''

RETURN = r'''
raw_output:
  description: The raw output of the specified task.
  type: str
  returned: success
  sample: |
    PLAY [localhost] ***********************************************************

    TASK [Gathering Facts] *****************************************************
    ok: [localhost]

    TASK [Print Hello World] ***************************************************
    ok: [localhost] => {
        "msg": "Hello World"
    }

    PLAY RECAP *****************************************************************
    localhost                  : ok=2    changed=0    unreachable=0    failed=0   
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

    url = f"{host}:{port}/api/project/{project_id}/tasks/{task_id}/raw_output"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "text/plain"

    try:
        response_body, status, _ = semaphore_get(
            url=url,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 200:
            module.fail_json(msg=f"Failed to retrieve task output: HTTP {status}", status=status)

        if isinstance(response_body, bytes):
            response_body = response_body.decode()

        module.exit_json(changed=False, raw_output=response_body)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

