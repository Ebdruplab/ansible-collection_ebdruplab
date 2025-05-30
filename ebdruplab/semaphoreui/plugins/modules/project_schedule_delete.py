#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_request, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_schedule_delete
short_description: Delete a schedule from a Semaphore project
version_added: "1.0.0"
description:
  - Deletes a schedule from the specified Semaphore project by ID.
options:
  host:
    description: Hostname or IP of the Semaphore server (including protocol).
    type: str
    required: true
  port:
    description: Port on which Semaphore is running.
    type: int
    required: true
  project_id:
    description: ID of the Semaphore project.
    type: int
    required: true
  schedule_id:
    description: ID of the schedule to delete.
    type: int
    required: true
  session_cookie:
    description: Session cookie obtained from the login module.
    type: str
    required: false
    no_log: true
  api_token:
    description: API token used for authentication.
    type: str
    required: false
    no_log: true
  validate_certs:
    description: Whether to validate TLS certificates.
    type: bool
    default: true
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Delete a schedule
  ebdruplab.semaphoreui.project_schedule_delete:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    schedule_id: 5
'''

RETURN = r'''
deleted:
  description: Whether the schedule was successfully deleted
  type: bool
  returned: always
status:
  description: HTTP status code from the Semaphore API
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
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[['session_cookie', 'api_token']],
        supports_check_mode=False
    )

    host = module.params['host'].rstrip('/')
    port = module.params['port']
    validate_certs = module.params['validate_certs']
    session_cookie = module.params.get('session_cookie')
    api_token = module.params.get('api_token')

    try:
        project_id = int(module.params['project_id'])
        schedule_id = int(module.params['schedule_id'])
    except Exception as e:
        module.fail_json(msg=f"Invalid numeric input: {str(e)}")

    url = f"{host}:{port}/api/project/{project_id}/schedules/{schedule_id}"

    headers = get_auth_headers(session_cookie=session_cookie, api_token=api_token)
    headers['Content-Type'] = 'application/json'

    # Including ID and project_id in DELETE body
    payload = {
        "id": schedule_id,
        "project_id": project_id
    }

    try:
        body = json.dumps(payload).encode("utf-8")
        _, status, _ = semaphore_request(
            method="DELETE",
            url=url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status not in (200, 204):
            module.fail_json(msg=f"Failed to delete schedule: HTTP {status}", status=status)

        module.exit_json(changed=True, deleted=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

