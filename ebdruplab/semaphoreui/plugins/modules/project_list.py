#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import get_auth_headers, semaphore_get
import json

DOCUMENTATION = r'''
---
module: project_list
short_description: Retrieve list of projects from Semaphore UI
version_added: "1.0.0"
description:
  - Retrieves the list of all projects using either a session cookie or API token.
options:
  host:
    description:
      - The host of the Semaphore API (e.g. http://localhost).
    required: true
    type: str
  port:
    description:
      - The port of the Semaphore API (e.g. 3000).
    required: true
    type: int
  session_cookie:
    description:
      - Session cookie obtained from login module (e.g. semaphore=abc123).
    required: false
    type: str
    no_log: true
  api_token:
    description:
      - API token string for bearer authentication.
    required: false
    type: str
    no_log: true
  validate_certs:
    description:
      - Whether to validate SSL certificates.
    type: bool
    default: true
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Get projects using session cookie
  ebdruplab.semaphoreui.project_list:
    host: http://localhost
    port: 3000
    session_cookie: "semaphore=abc123"

- name: Get projects using API token
  ebdruplab.semaphoreui.project_list:
    host: http://localhost
    port: 3000
    api_token: "abcd.1234.yourtoken"
'''

RETURN = r'''
projects:
  description: List of projects returned by Semaphore.
  type: list
  elements: dict
  returned: always
'''

def main():
    argument_spec = dict(
        host=dict(type='str', required=True),
        port=dict(type='int', required=True),
        session_cookie=dict(type='str', required=False, no_log=True),
        api_token=dict(type='str', required=False, no_log=True),
        validate_certs=dict(type='bool', default=True)
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[['session_cookie', 'api_token']],
        supports_check_mode=True
    )

    host = module.params['host'].rstrip('/')
    port = module.params['port']
    session_cookie = module.params.get('session_cookie')
    api_token = module.params.get('api_token')
    validate_certs = module.params['validate_certs']

    url = f"{host}:{port}/api/projects"

    try:
        headers = get_auth_headers(session_cookie, api_token)
        headers["Accept"] = "application/json"

        response_body, status, _ = semaphore_get(url, headers=headers, validate_certs=validate_certs)

        if status != 200:
            module.fail_json(msg=f"Failed to fetch projects: HTTP {status}", response=response_body)

        projects = json.loads(response_body)
        module.exit_json(changed=False, projects=projects)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

