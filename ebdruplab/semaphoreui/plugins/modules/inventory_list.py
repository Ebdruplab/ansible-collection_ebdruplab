from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: inventory_list
short_description: List inventories for a Semaphore project
version_added: "1.0.0"
description:
  - Retrieves all inventories associated with a specific Semaphore project.
options:
  host:
    type: str
    required: true
    description: Full host address of the Semaphore server (including http/https).
  port:
    type: int
    required: true
    description: Port of the Semaphore server (e.g., 3000).
  project_id:
    type: int
    required: true
    description: ID of the project whose inventories you want to list.
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
- name: List inventories for a project
  ebdruplab.semaphoreui.inventory_list:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
'''

RETURN = r'''
inventories:
  description: List of inventory objects associated with the project
  type: list
  returned: success
  sample:
    - id: 1
      name: Default Inventory
      type: static
      ...
'''

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
