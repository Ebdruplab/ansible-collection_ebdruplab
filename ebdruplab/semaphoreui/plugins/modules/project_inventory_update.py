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
    type: str
    required: true
  port:
    type: int
    required: true
  project_id:
    type: int
    required: true
  inventory_id:
    type: int
    required: true
  inventory:
    type: dict
    required: true
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
- name: Update an inventory
  ebdruplab.semaphoreui.project_inventory_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    inventory_id: 2
    inventory:
      name: "Updated Inventory"
      type: "static"
      inventory: |
        localhost ansible_connection=local
'''

RETURN = r'''
inventory:
  description: The updated inventory (if returned by the API).
  type: dict
  returned: when available
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            inventory_id=dict(type='int', required=True),
            inventory=dict(type='dict', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True)
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    host = module.params["host"]
    port = module.params["port"]
    project_id = module.params["project_id"]
    inventory_id = module.params["inventory_id"]

    url = f"{host}:{port}/api/project/{project_id}/inventory/{inventory_id}"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    payload = module.params["inventory"]
    payload["project_id"] = project_id
    payload["id"] = inventory_id

    try:
        body = json.dumps(payload).encode("utf-8")
        response_body, status, _ = semaphore_put(
            url,
            body=body,
            headers=headers,
            validate_certs=module.params["validate_certs"]
        )

        if status == 204:
            # Update succeeded, but no body returned
            module.exit_json(changed=True, inventory=None, status=status)
        elif status == 200:
            inventory = json.loads(response_body) if isinstance(response_body, bytes) else json.loads(response_body)
            module.exit_json(changed=True, inventory=inventory)
        else:
            module.fail_json(msg=f"Failed to update inventory: HTTP {status} - {response_body}", status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
