#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_inventory_update
short_description: Update an inventory in Semaphore
version_added: "1.0.0"
description:
  - Updates an existing inventory inside a Semaphore project.
options:
  host:
    description:
      - Hostname of the Semaphore server (including http/https).
    type: str
    required: true
  port:
    description:
      - Port on which the Semaphore API is running.
    type: int
    required: true
  project_id:
    description:
      - ID of the project containing the inventory.
    type: int
    required: true
  inventory_id:
    description:
      - ID of the inventory to update.
    type: int
    required: true
  inventory:
    description:
      - Dictionary containing the updated inventory fields.
      - May include ssh_key_id (user credentials) and become_key_id (sudo credentials).
      - For type 'file', include repository_id and inventory_file (or inventory path).
    type: dict
    required: true
    suboptions:
      name:
        description: Name of the inventory.
        type: str
      type:
        description: Inventory type.
        type: str
        choices: [static, static-yaml, file]
      inventory:
        description: For static/static-yaml, the content. For file, the file path.
        type: str
      inventory_file:
        description: Alias for file path when type is 'file'.
        type: str
      repository_id:
        description: Repository ID when type is 'file'.
        type: int
      ssh_key_id:
        description: SSH key (user credentials) to use.
        type: int
        version_added: 2.0.0
      become_key_id:
        description: Become (sudo) key to use.
        type: int
        version_added: 2.0.0
  session_cookie:
    description:
      - Session cookie for authentication.
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - Bearer token for authentication.
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
- name: Update an inventory (change name and attach creds)
  ebdruplab.semaphoreui.project_inventory_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    inventory_id: 2
    inventory:
      name: "Updated Inventory"
      ssh_key_id: 42
      become_key_id: 7
'''

RETURN = r'''
inventory:
  description: The updated inventory object (if returned by the API, or the payload for 204 responses).
  type: dict
  returned: success
status:
  description: HTTP response code returned by the API.
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
            inventory=dict(
                type='dict',
                required=True,
                options=dict(
                    name=dict(type='str', required=False),
                    type=dict(type='str', required=False, choices=['static', 'static-yaml', 'file']),
                    inventory=dict(type='str', required=False),
                    inventory_file=dict(type='str', required=False),
                    repository_id=dict(type='int', required=False),
                    ssh_key_id=dict(type='int', required=False),
                    become_key_id=dict(type='int', required=False),
                ),
            ),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True)
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    try:
        host = module.params["host"].rstrip("/")
        port = module.params["port"]
        project_id = module.params["project_id"]
        inventory_id = module.params["inventory_id"]

        url = f"{host}:{port}/api/project/{project_id}/inventory/{inventory_id}"

        headers = get_auth_headers(
            session_cookie=module.params.get("session_cookie"),
            api_token=module.params.get("api_token")
        )
        headers["Content-Type"] = "application/json"

        # Start with validated dict
        payload = dict(module.params["inventory"] or {})
        payload["project_id"] = project_id
        payload["id"] = inventory_id

        # Normalize file path alias if provided
        if payload.get("type") == "file" and payload.get("inventory_file"):
            payload["inventory"] = payload.pop("inventory_file")

        # Only set inventory_mode if 'type' is being updated
        if "type" in payload:
            inv_type = payload["type"]
            if inv_type == "static":
                payload["inventory_mode"] = "text"
            elif inv_type == "static-yaml":
                payload["inventory_mode"] = "yaml"
            elif inv_type == "file":
                payload["inventory_mode"] = "file"

        # Do the PUT
        body = json.dumps(payload).encode("utf-8")
        response_body, status, _ = semaphore_put(
            url,
            body=body,
            headers=headers,
            validate_certs=module.params["validate_certs"]
        )

        if status == 204:
            # No content, return what we sent
            module.exit_json(changed=True, inventory=payload, status=status)

        if isinstance(response_body, (bytes, bytearray)):
            text = response_body.decode() or ""
        elif isinstance(response_body, str):
            text = response_body
        else:
            module.exit_json(changed=True, inventory=response_body, status=status)

        if status == 200:
            try:
                inventory = json.loads(text) if text else {}
            except Exception:
                inventory = {"raw": text}
            module.exit_json(changed=True, inventory=inventory, status=status)

        module.fail_json(msg=f"Failed to update inventory: HTTP {status} - {text}", status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
