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
    type: str
    required: true
  port:
    type: int
    required: true
  project_id:
    type: int
    required: true
  inventory:
    type: dict
    required: true
    description: Dictionary describing the inventory.
  session_cookie:
    type: str
    required: false
    no_log: true
  api_token:
    type: str
    required: false
    no_log: true
  validate_certs:
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

- name: Create YAML static inventory
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
            inventory=dict(type='dict', required=True),
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
    inventory_data = module.params["inventory"]
    inventory_data["project_id"] = project_id

    # Normalize inventory_file to inventory for type "file"
    if inventory_data.get("type") == "file" and "inventory_file" in inventory_data:
        inventory_data["inventory"] = inventory_data.pop("inventory_file")

    # Validate type
    valid_types = ["static", "static-yaml", "file"]
    inventory_type = inventory_data.get("type")
    if inventory_type not in valid_types:
        module.fail_json(msg=f"Invalid or missing inventory type. Must be one of: {', '.join(valid_types)}")

    # Configure inventory_mode and validate required fields
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
        try:
            inventory_data["repository_id"] = int(inventory_data["repository_id"])
        except ValueError:
            module.fail_json(msg="'repository_id' must be an integer")
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

        result = json.loads(response_body)
        module.exit_json(changed=True, inventory=result)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

