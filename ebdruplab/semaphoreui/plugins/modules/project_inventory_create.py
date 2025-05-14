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
- name: Create inventory
  ebdruplab.semaphoreui.project_inventory_create:
    host: localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    inventory:
      name: "Local Inventory"
      type: "static"
      inventory: |
        localhost ansible_connection=local
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

    host = module.params["host"]
    port = module.params["port"]
    url = f"{host}:{port}/api/project/{module.params['project_id']}/inventory"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    inventory_data = module.params["inventory"]
    inventory_data["project_id"] = module.params["project_id"]

    # Validate `type` field
    valid_types = ["static", "static-yaml", "file"]
    if "type" not in inventory_data or inventory_data["type"] not in valid_types:
        module.fail_json(msg=f"Invalid or missing inventory type. Must be one of: {', '.join(valid_types)}")

    try:
        body = json.dumps(inventory_data).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url,
            body=body,
            headers=headers,
            validate_certs=module.params["validate_certs"]
        )

        if status not in (200, 201):
            module.fail_json(msg=f"Failed to create inventory: HTTP {status} - {response_body.decode()}")

        result = json.loads(response_body)
        module.exit_json(changed=True, inventory=result)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
