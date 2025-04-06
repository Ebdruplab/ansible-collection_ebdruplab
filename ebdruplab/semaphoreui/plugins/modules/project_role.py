# plugins/modules/project_role.py

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
    type: str
    required: true
  port:
    type: int
    required: true
  project_id:
    type: int
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
  - Kristian Ebdrup @kris9854
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
  returned: always
  type: str
permissions:
  description: Bitmask integer describing user permissions
  returned: always
  type: int
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

    url = f"{module.params['host']}:{module.params['port']}/api/project/{module.params['project_id']}/role"

    try:
        headers = get_auth_headers(
            module.params['session_cookie'],
            module.params['api_token']
        )

        response_body, status, _ = semaphore_get(url, headers=headers, validate_certs=module.params["validate_certs"])

        if status != 200:
            module.fail_json(msg=f"Failed to fetch project role: HTTP {status} - {response_body}")

        role_data = json.loads(response_body)
        module.exit_json(changed=False, **role_data)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
