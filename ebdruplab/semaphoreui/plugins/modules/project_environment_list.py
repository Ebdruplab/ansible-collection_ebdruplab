#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_environment_list
short_description: List environments in a Semaphore project
version_added: "1.0.0"
description:
  - Retrieves all environments associated with a given Semaphore project.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server, including protocol (e.g., http://localhost).
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
  sort:
    description:
      - Field to sort the environments by.
    type: str
    default: name
    choices: ["name"]
  order:
    description:
      - Sort order direction.
    type: str
    default: desc
    choices: ["asc", "desc"]
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
- name: List environments in a project
  ebdruplab.semaphoreui.project_environment_list:
    host: http://localhost
    port: 3000
    project_id: 1
    session_cookie: "{{ login_result.session_cookie }}"

- name: List environments sorted ascending
  ebdruplab.semaphoreui.project_environment_list:
    host: http://localhost
    port: 3000
    project_id: 1
    order: asc
    api_token: "{{ token }}"
"""

RETURN = r"""
environments:
  description: List of environment objects.
  type: list
  elements: dict
  returned: success
  sample:
    - id: 4
      name: "Development"
      project_id: 1
      env: '{"DEBUG": "true"}'
      json: '{"extra": "data"}'
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            sort=dict(type='str', default='name', choices=['name']),
            order=dict(type='str', default='desc', choices=['asc', 'desc']),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    sort = module.params["sort"]
    order = module.params["order"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/environment?sort={sort}&order={order}"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )

    try:
        response_body, status, _ = semaphore_get(
            url=url,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 200:
            module.fail_json(msg=f"Failed to list environments: HTTP {status}", status=status)

        environments = json.loads(response_body)
        module.exit_json(changed=False, environments=environments)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

