#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r'''
---
module: project_inventory_delete
short_description: Delete a Semaphore inventory
version_added: "1.0.0"
description:
  - Deletes an inventory from a Semaphore project.
options:
  host:
    description:
      - Hostname of the Semaphore server, including protocol (e.g. http://localhost).
    type: str
    required: true
  port:
    description:
      - Port of the Semaphore server (e.g. 3000).
    type: int
    required: true
  project_id:
    description:
      - The ID of the project the inventory belongs to.
    type: int
    required: true
  inventory_id:
    description:
      - The ID of the inventory to delete.
    type: int
    required: true
  session_cookie:
    description:
      - Session cookie used for authentication.
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - API token used for authentication.
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
- name: Delete inventory
  ebdruplab.semaphoreui.project_inventory_delete:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    inventory_id: 5
'''

RETURN = r'''
deleted:
  description: Whether the inventory was successfully deleted.
  type: bool
  returned: always
status:
  description: HTTP response code from the API.
  type: int
  returned: always
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            inventory_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params['host']
    port = module.params['port']
    project_id = module.params['project_id']
    inventory_id = module.params['inventory_id']

    url = f"{host}:{port}/api/project/{project_id}/inventory/{inventory_id}"

    try:
        headers = get_auth_headers(
            session_cookie=module.params.get("session_cookie"),
            api_token=module.params.get("api_token")
        )

        _, status, _ = semaphore_delete(
            url,
            headers=headers,
            validate_certs=module.params["validate_certs"]
        )

        if status not in (200, 204):
            module.fail_json(msg=f"Failed to delete inventory: HTTP {status}", status=status)

        module.exit_json(changed=True, deleted=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

