#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r"""
---
module: project_environment_delete
short_description: Delete an environment in a Semaphore project
version_added: "1.0.0"
description:
  - Deletes a specific environment from a Semaphore project using its environment ID.
options:
  host:
    description:
      - Hostname or IP address of the Semaphore server, including protocol (e.g., http://localhost).
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
      - ID of the environment to delete.
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
- name: Delete a Semaphore project environment
  ebdruplab.semaphoreui.project_environment_delete:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    environment_id: 5

- name: Delete environment with API token
  ebdruplab.semaphoreui.project_environment_delete:
    host: http://localhost
    port: 3000
    api_token: "{{ token }}"
    project_id: 2
    environment_id: 10
"""

RETURN = r"""
deleted:
  description: Whether the environment was successfully deleted.
  type: bool
  returned: always
  sample: true

status:
  description: HTTP status code returned by the Semaphore API.
  type: int
  returned: always
  sample: 204
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            environment_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True)
        ),
        required_one_of=[['session_cookie', 'api_token']],
        supports_check_mode=False
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    environment_id = module.params["environment_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/environment/{environment_id}"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        _, status, _ = semaphore_delete(url, headers=headers, validate_certs=validate_certs)

        if status != 204:
            module.fail_json(msg=f"Failed to delete environment: HTTP {status}", status=status)

        module.exit_json(changed=True, deleted=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

