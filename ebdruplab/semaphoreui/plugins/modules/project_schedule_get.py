#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_schedule_get
short_description: Get a schedule by ID for a Semaphore project
version_added: "1.0.0"
description:
  - Retrieves a specific schedule from a Semaphore project.
options:
  host:
    description: Hostname or IP of the Semaphore server (with protocol).
    type: str
    required: true
  port:
    description: Port number where the Semaphore API is listening.
    type: int
    required: true
  project_id:
    description: ID of the project that the schedule belongs to.
    type: int
    required: true
  schedule_id:
    description: ID of the schedule to retrieve.
    type: int
    required: true
  session_cookie:
    description: Session authentication cookie.
    type: str
    required: false
    no_log: true
  api_token:
    description: API token for authentication.
    type: str
    required: false
    no_log: true
  validate_certs:
    description: Whether to validate SSL/TLS certificates.
    type: bool
    default: true
author:
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: Get a schedule
  ebdruplab.semaphoreui.project_schedule_get:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    schedule_id: 5
'''

RETURN = r'''
schedule:
  description: The schedule object retrieved from the API.
  type: dict
  returned: always
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            schedule_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    validate_certs = module.params["validate_certs"]

    try:
        project_id = int(module.params["project_id"])
        schedule_id = int(module.params["schedule_id"])
    except Exception as e:
        module.fail_json(msg=f"Invalid numeric input: {e}")

    url = f"{host}:{port}/api/project/{project_id}/schedules/{schedule_id}"

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
            msg = response_body if isinstance(response_body, str) else response_body.decode()
            module.fail_json(msg=f"Failed to fetch schedule: HTTP {status} - {msg}", status=status)

        schedule = json.loads(response_body)
        module.exit_json(changed=False, schedule=schedule)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

