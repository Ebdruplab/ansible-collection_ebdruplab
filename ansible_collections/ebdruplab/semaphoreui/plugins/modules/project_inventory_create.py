#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_inventory_create
short_description: Create an inventory in Semaphore
version_added: "1.0.0"
description:
  - Creates an inventory inside a Semaphore project.
  - Supports static text, static YAML, or file-based inventory from a repository.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (with protocol).
    type: str
    required: true
  port:
    description:
      - Port of the Semaphore server (e.g., 3000).
    type: int
    required: true
  project_id:
    description:
      - ID of the Semaphore project.
    type: int
    required: true
  inventory:
    description:
      - Dictionary describing the inventory.
      - Must include ssh_key_id (user credentials) and may include become_key_id (sudo credentials).
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
        required: true
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
        required: true
        version_added: 2.0.0
      become_key_id:
        description: Become (sudo) key to use.
        type: int
        version_added: 2.0.0
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
- name: Create static inventory
  ebdruplab.semaphoreui.project_inventory_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    inventory:
      name: "Local Static Inventory"
      type: "static"
      inventory: "localhost ansible_connection=local"
      ssh_key_id: 42
      become_key_id: 7

- name: Create YAML static inventory (no become)
  ebdruplab.semaphoreui.project_inventory_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    inventory:
      name: "Static YAML Inventory"
      type: "static-yaml"
      inventory: |
        all:
          hosts:
            localhost:
              ansible_connection: local
      ssh_key_id: 42

- name: Create repository file-based inventory
  ebdruplab.semaphoreui.project_inventory_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    inventory:
      name: "Git Inventory"
      type: "file"
      repository_id: 12
      inventory_file: "inventories/production.ini"
      ssh_key_id: 42
      become_key_id: 7
'''

RETURN = r'''
inventory:
  description: The created inventory object.
  type: dict
  returned: success
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            inventory=dict(
                type='dict',
                required=True,
                options=dict(
                    name=dict(type='str', required=False),
                    type=dict(type='str', required=True, choices=['static', 'static-yaml', 'file']),
                    inventory=dict(type='str', required=False),
                    inventory_file=dict(type='str', required=False),
                    repository_id=dict(type='int', required=False),
                    ssh_key_id=dict(type='int', required=True),
                    become_key_id=dict(type='int', required=False),
                ),
            ),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    validate_certs = module.params["validate_certs"]

    # Work directly with the provided dict (Ansible has already validated presence/types)
    inventory_data = dict(module.params["inventory"])
    inventory_data["project_id"] = project_id

    # Normalize file path alias if provided
    if inventory_data.get("type") == "file" and inventory_data.get("inventory_file"):
        inventory_data["inventory"] = inventory_data.pop("inventory_file")

    valid_types = ["static", "static-yaml", "file"]
    inventory_type = inventory_data.get("type")

    if inventory_type not in valid_types:
        module.fail_json(msg=f"Invalid or missing inventory type. Must be one of: {', '.join(valid_types)}")

    if inventory_type == "static":
        if "inventory" not in inventory_data:
            module.fail_json(msg="Missing 'inventory' content for type 'static'")
        inventory_data["inventory_mode"] = "text"

    elif inventory_type == "static-yaml":
        if "inventory" not in inventory_data:
            module.fail_json(msg="Missing 'inventory' YAML content for type 'static-yaml'")
        inventory_data["inventory_mode"] = "yaml"

    elif inventory_type == "file":
        if "repository_id" not in inventory_data or "inventory" not in inventory_data:
            module.fail_json(msg="Missing 'repository_id' or 'inventory' (file path) for type 'file'")
        # repository_id already typed as int by Ansible
        inventory_data["inventory_mode"] = "file"

    url = f"{host}:{port}/api/project/{project_id}/inventory"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        body = json.dumps(inventory_data).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status not in (200, 201):
            error = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"Failed to create inventory: HTTP {status} - {error}")

        # response_body may be bytes; json.loads accepts str
        result = json.loads(response_body.decode() if isinstance(response_body, (bytes, bytearray)) else response_body)
        module.exit_json(changed=True, inventory=result)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
