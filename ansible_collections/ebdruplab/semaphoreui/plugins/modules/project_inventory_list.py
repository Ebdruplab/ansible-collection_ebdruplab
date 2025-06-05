#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

DOCUMENTATION = r"""
---
module: project_inventory_list
short_description: List inventories for a Semaphore project
version_added: "1.0.0"
description:
  - Retrieves all inventories associated with a specific Semaphore project.
options:
  host:
    description:
      - Full host address of the Semaphore server (including http or https).
    required: true
    type: str
  port:
    description:
      - Port of the Semaphore server (e.g., 3000).
    required: true
    type: int
  project_id:
    description:
      - ID of the project whose inventories you want to list.
    required: true
    type: int
  session_cookie:
    description:
      - Session cookie used for authentication.
    required: false
    type: str
    no_log: true
  api_token:
    description:
      - API token used for authentication.
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
- name: List inventories for a project
  ebdruplab.semaphoreui.project_inventory_list:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
"""

RETURN = r"""
inventories:
  description: List of inventory objects associated with the project
  type: list
  returned: success
  sample:
    - id: 1
      name: Default Inventory
      type: static
"""

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True)
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params["host"]
    port = module.params["port"]
    project_id = module.params["project_id"]

    url = f"{host}:{port}/api/project/{project_id}/inventory"

    try:
        headers = get_auth_headers(
            session_cookie=module.params.get("session_cookie"),
            api_token=module.params.get("api_token")
        )

        response_body, status, _ = semaphore_get(
            url,
            headers=headers,
            validate_certs=module.params["validate_certs"]
        )

        if status != 200:
            module.fail_json(msg=f"Failed to list inventories: HTTP {status}", status=status)

        inventories = json.loads(response_body)
        module.exit_json(changed=False, inventories=inventories)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

