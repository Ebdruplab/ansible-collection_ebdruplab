#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_schedule_create
short_description: Create a schedule for a Semaphore project
version_added: "1.0.0"
description:
  - Sends a POST request to create a new schedule for a specified project in Semaphore.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (including protocol).
    type: str
    required: true
  port:
    description:
      - Port on which the Semaphore API is listening.
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
      - API token used for authentication.
    type: str
    required: false
    no_log: true
  project_id:
    description:
      - ID of the project to associate the schedule with.
    type: int
    required: true
  schedule:
    description:
      - Dictionary containing schedule details.
    type: dict
    required: true
    suboptions:
      cron_format:
        description:
          - Cron format string defining the schedule (e.g., "* * * * *").
        type: str
        required: true
      template_id:
        description:
          - ID of the template to run with this schedule.
        type: int
        required: true
      name:
        description:
          - Name of the schedule.
        type: str
        required: true
      active:
        description:
          - Whether the schedule is active.
        type: bool
        required: false
        default: true
  validate_certs:
    description:
      - Whether to validate TLS certificates.
    type: bool
    default: true
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Create a schedule
  ebdruplab.semaphoreui.project_schedule_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    schedule:
      cron_format: "* * * * *"
      template_id: 1
      name: "My Schedule"
      active: true
'''

RETURN = r'''
schedule:
  description:
    - The created schedule object returned from the Semaphore API.
  type: dict
  returned: success
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            project_id=dict(type='int', required=True),
            schedule=dict(type='dict', required=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    p = module.params
    host = p["host"].rstrip("/")
    port = p["port"]
    project_id = p["project_id"]
    schedule = p["schedule"]
    validate_certs = p["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/schedules"

    headers = get_auth_headers(
        session_cookie=p.get("session_cookie"),
        api_token=p.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        payload = {
            "cron_format": schedule["cron_format"],
            "template_id": schedule["template_id"],
            "name": schedule["name"],
            "active": schedule.get("active", True)
        }

        body = json.dumps(payload).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url=url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status not in (200, 201):
            msg = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"POST failed with status {status}: {msg}", status=status)

        schedule_data = json.loads(response_body)
        module.exit_json(changed=True, schedule=schedule_data)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

