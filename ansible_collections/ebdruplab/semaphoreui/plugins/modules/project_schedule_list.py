#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_schedule_list
short_description: List schedules for a Semaphore project
version_added: "1.0.0"
description:
  - Retrieves a list of schedules defined under a specified Semaphore project.
options:
  host:
    description:
      - Hostname or IP (including protocol) of the Semaphore server.
    type: str
    required: true
  port:
    description:
      - Port number on which the Semaphore server is listening.
    type: int
    required: true
  project_id:
    description:
      - ID of the project whose schedules to list.
    type: int
    required: true
  session_cookie:
    description:
      - Authentication cookie from login module.
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - Bearer token for API authentication.
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - Whether to validate SSL certificates.
    type: bool
    default: true
author:
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: List schedules for a project
  ebdruplab.semaphoreui.project_schedule_list:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
  register: schedule_list

- name: Show schedules
  debug:
    var: schedule_list.schedules
'''

RETURN = r'''
schedules:
  description: List of schedule objects for the project.
  type: list
  returned: success
status:
  description: HTTP status code returned by the API.
  type: int
  returned: always
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[['session_cookie', 'api_token']],
        supports_check_mode=True
    )

    host = module.params['host'].rstrip('/')
    port = module.params['port']
    project_id = module.params['project_id']
    validate_certs = module.params['validate_certs']
    session_cookie = module.params.get('session_cookie')
    api_token = module.params.get('api_token')

    url = f"{host}:{port}/api/project/{project_id}/schedule"

    try:
        headers = get_auth_headers(session_cookie=session_cookie, api_token=api_token)
        headers['Content-Type'] = 'application/json'

        response_body, status, _ = semaphore_get(
            url,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 200:
            msg = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"Failed to list schedules: HTTP {status} - {msg}", status=status)

        schedules = json.loads(response_body)
        if not isinstance(schedules, list):
            module.fail_json(msg="Unexpected response format: schedules is not a list")

        module.exit_json(changed=False, schedules=schedules, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

