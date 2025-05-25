#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers

DOCUMENTATION = r'''
---
module: project_inventory_get
short_description: Retrieve a specific inventory from a Semaphore project
version_added: "1.0.0"
description:
  - Fetches details of a single inventory resource within a given Semaphore project.
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
      - ID of the project containing the inventory.
    type: int
    required: true
  inventory_id:
    description:
      - ID of the inventory to retrieve.
    type: int
    required: true
  session_cookie:
    description:
      - Authentication cookie returned by the login module.
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
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Get a specific inventory
  ebdruplab.semaphoreui.project_inventory_get:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    inventory_id: 42
  register: inventory_data

- name: Dump inventory
  debug:
    var: inventory_data.inventory
'''

RETURN = r'''
inventory:
  description: Details of the requested inventory.
  type: dict
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
            inventory_id=dict(type='int', required=True),
            session_cookie=dict(type='str', no_log=True),
            api_token=dict(type='str', no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[['session_cookie', 'api_token']],
        supports_check_mode=True
    )

    host = module.params['host'].rstrip('/')
    port = module.params['port']
    project_id = module.params['project_id']
    inventory_id = module.params['inventory_id']
    validate_certs = module.params['validate_certs']
    session_cookie = module.params.get('session_cookie')
    api_token = module.params.get('api_token')

    url = f"{host}:{port}/api/project/{project_id}/inventory/{inventory_id}"

    try:
        headers = get_auth_headers(session_cookie=session_cookie, api_token=api_token)
        headers['Content-Type'] = 'application/json'

        response_body, status, _ = semaphore_get(
            url,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 200:
            module.fail_json(msg=f"Failed to retrieve inventory: HTTP {status}", status=status)

        module.exit_json(changed=False, inventory=response_body, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

