#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_schedule_update
short_description: Update a schedule in a Semaphore project
version_added: "1.0.0"
description:
  - Updates a schedule for a given project in Semaphore by ID.
options:
  host:
    description:
      - Hostname or IP address of the Semaphore server (including protocol).
    type: str
    required: true
  port:
    description:
      - Port where the Semaphore API is available (e.g. 3000).
    type: int
    required: true
  project_id:
    description:
      - ID of the project that owns the schedule.
    type: int
    required: true
  schedule_id:
    description:
      - ID of the schedule to update.
    type: int
    required: true
  schedule:
    description:
      - Dictionary containing the updated schedule fields.
    type: dict
    required: true
  session_cookie:
    description:
      - Session cookie for authentication.
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - API token for authentication.
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - Whether to validate TLS certificates.
    type: bool
    default: true
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Update a schedule
  ebdruplab.semaphoreui.project_schedule_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    schedule_id: 5
    schedule:
      name: "Updated Schedule"
      cron_format: "0 * * * *"
      template_id: 1
      active: true
'''

RETURN = r'''
updated:
  description:
    - Whether the schedule was successfully updated.
  type: bool
  returned: always
schedule:
  description:
    - The updated schedule object returned from the API.
  type: dict
  returned: success
status:
  description:
    - HTTP status code from the Semaphore API.
  type: int
  returned: always
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            schedule_id=dict(type='int', required=True),
            schedule=dict(type='dict', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    validate_certs = module.params["validate_certs"]
    schedule_data = module.params["schedule"]

    try:
        project_id = int(module.params["project_id"])
        schedule_id = int(module.params["schedule_id"])
    except Exception as e:
        module.fail_json(msg=f"Invalid numeric input: {str(e)}")

    url = f"{host}:{port}/api/project/{project_id}/schedules/{schedule_id}"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    payload = {
        "id": schedule_id,
        "project_id": project_id,
        "name": str(schedule_data.get("name")),
        "cron_format": str(schedule_data.get("cron_format")),
        "template_id": int(schedule_data.get("template_id")),
        "active": bool(schedule_data.get("active", True)),
    }

    try:
        body = json.dumps(payload).encode("utf-8")
        _, put_status, _ = semaphore_put(
            url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if put_status not in (200, 204):
            module.fail_json(msg=f"PUT failed with status {put_status}", status=put_status)

        # GET updated schedule
        response_body, get_status, _ = semaphore_get(
            url,
            headers=headers,
            validate_certs=validate_certs
        )

        if get_status != 200:
            module.fail_json(msg=f"GET after update failed with status {get_status}", status=get_status)

        schedule_obj = json.loads(response_body)
        module.exit_json(changed=True, updated=True, schedule=schedule_obj, status=put_status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

