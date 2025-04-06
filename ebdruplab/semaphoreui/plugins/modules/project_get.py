# plugins/modules/project_get.py

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_get
short_description: Fetch project details
version_added: "1.0.0"
description:
  - Retrieves a specific project's details by ID.
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
- name: Get project by ID
  ebdruplab.semaphoreui.project_get:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
'''

RETURN = r'''
project:
  description: The project object returned by Semaphore
  type: dict
  returned: always
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
        required_one_of=[['session_cookie', 'api_token']],
        supports_check_mode=True
    )

    url = f"{module.params['host']}:{module.params['port']}/api/project/{module.params['project_id']}"

    try:
        headers = get_auth_headers(
            session_cookie=module.params["session_cookie"],
            api_token=module.params["api_token"]
        )

        body, status, _ = semaphore_get(url, headers=headers, validate_certs=module.params["validate_certs"])

        if status != 200:
            module.fail_json(msg=f"Failed to get project: HTTP {status} - {body}")

        module.exit_json(changed=False, project=json.loads(body))

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
