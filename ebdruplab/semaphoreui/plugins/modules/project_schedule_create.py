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
  - Creates a new scheduled task (cron job) in a specified Semaphore project using a defined template.
  - Requires authentication via session cookie or API token.
options:
  host:
    description:
      - Hostname or IP address of the Semaphore server (e.g. C(http://localhost)).
    type: str
    required: true
  port:
    description:
      - Port number where the Semaphore API is accessible (e.g. C(3000)).
    type: int
    required: true
  session_cookie:
    description:
      - Session cookie for authenticating the user session.
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - API token for authenticating the user instead of a session cookie.
    type: str
    required: false
    no_log: true
  project_id:
    description:
      - ID of the Semaphore project in which to create the schedule.
    type: int
    required: true
  schedule:
    description:
      - Dictionary containing the schedule details.
    type: dict
    required: true
    suboptions:
      cron_format:
        description:
          - Cron expression defining when the schedule runs.
        type: str
        required: true
      template_id:
        description:
          - ID of the template to be used when the schedule triggers.
        type: int
        required: true
      name:
        description:
          - Human-readable name for the schedule.
        type: str
        required: true
      active:
        description:
          - Whether the schedule is active.
        type: bool
        default: true
  validate_certs:
    description:
      - Whether to validate TLS certificates when using HTTPS.
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
    - The created schedule object as returned by the Semaphore API.
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

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    schedule = module.params["schedule"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/schedules"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        payload = {
            "cron_format": str(schedule["cron_format"]),
            "template_id": int(schedule["template_id"]),
            "name": str(schedule["name"]),
            "active": bool(schedule.get("active", True))
        }

        body = json.dumps(payload).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status not in (200, 201):
            msg = response_body if isinstance(response_body, str) else response_body.decode()
            module.fail_json(msg=f"POST failed with status {status}: {msg}", status=status)

        schedule_response = json.loads(response_body)
        module.exit_json(changed=True, schedule=schedule_response)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

