#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_role
short_description: Get user role and permissions for a Semaphore project
version_added: "1.0.0"
description:
  - Fetches the current user's role and permission level for the specified project.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (with http or https).
    type: str
    required: true
  port:
    description:
      - Port number the Semaphore API is listening on.
    type: int
    required: true
  project_id:
    description:
      - ID of the Semaphore project.
    type: int
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
- name: Fetch project role for current user
  ebdruplab.semaphoreui.project_role:
    host: http://localhost
    port: 3000
    api_token: "abcd1234"
    project_id: 1
'''

RETURN = r'''
role:
  description: The user's role in the project (e.g., owner, admin, etc.)
  type: str
  returned: always
permissions:
  description: Bitmask integer describing user permissions.
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
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/role"

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
            module.fail_json(msg=f"Failed to fetch project role: HTTP {status}", response=response_body)

        try:
            role_data = json.loads(response_body)
        except json.JSONDecodeError:
            module.fail_json(msg="Invalid JSON returned from server", raw=response_body)

        if not isinstance(role_data, dict) or "role" not in role_data or "permissions" not in role_data:
            module.fail_json(msg="Malformed project role data", response=role_data)

        module.exit_json(changed=False, **role_data)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

