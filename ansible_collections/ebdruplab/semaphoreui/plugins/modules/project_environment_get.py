#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_environment_get
short_description: Retrieve a specific environment from a Semaphore project
version_added: "1.0.0"
description:
  - Fetches the details of a specific environment by ID within a Semaphore project.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (including http/https).
    required: true
    type: str
  port:
    description:
      - Port where the Semaphore API is running.
    required: true
    type: int
  project_id:
    description:
      - ID of the Semaphore project.
    required: true
    type: int
  environment_id:
    description:
      - ID of the environment to retrieve.
    required: true
    type: int
  session_cookie:
    description:
      - Session authentication cookie.
    required: false
    type: str
    no_log: true
  api_token:
    description:
      - Bearer token for authentication.
    required: false
    type: str
    no_log: true
  validate_certs:
    description:
      - Whether to validate TLS certificates.
    required: false
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Retrieve a project environment
  ebdruplab.semaphoreui.project_environment_get:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    environment_id: 4
  register: env_info

- name: Show environment details
  debug:
    var: env_info.environment
"""

RETURN = r"""
environment:
  description: Details of the requested environment.
  type: dict
  returned: success
  sample:
    id: 4
    name: "Production"
    env: '{"KEY": "VALUE"}'
    json: '{"config": "abc"}'
    project_id: 1

status:
  description: HTTP status code from the Semaphore API.
  type: int
  returned: always
  sample: 200
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            environment_id=dict(type='int', required=True),
            session_cookie=dict(type='str', no_log=True),
            api_token=dict(type='str', no_log=True),
            validate_certs=dict(type='bool', default=True)
        ),
        required_one_of=[['session_cookie', 'api_token']],
        supports_check_mode=True
    )

    host = module.params['host'].rstrip('/')
    port = module.params['port']
    project_id = module.params['project_id']
    environment_id = module.params['environment_id']
    validate_certs = module.params['validate_certs']

    url = f"{host}:{port}/api/project/{project_id}/environment/{environment_id}"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        response_body, status, _ = semaphore_get(
            url,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 200:
            module.fail_json(msg=f"Failed to retrieve environment: HTTP {status}", status=status)

        environment = json.loads(response_body)
        module.exit_json(changed=False, environment=environment, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

