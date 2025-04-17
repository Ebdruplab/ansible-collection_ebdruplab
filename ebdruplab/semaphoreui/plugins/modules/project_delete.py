# plugins/modules/project_delete.py

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r'''
---
module: project_delete
short_description: Delete a Semaphore project
version_added: "1.0.0"
description:
  - Deletes a project from the Semaphore server using the project ID.
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
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Delete a Semaphore project
  ebdruplab.semaphoreui.project_delete:
    host: http://localhost
    port: 3000
    api_token: "your_api_token"
    project_id: 1
'''

RETURN = r'''
deleted:
  description: Whether the project was successfully deleted
  type: bool
  returned: always
status:
  description: HTTP response code
  type: int
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
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params["host"]
    port = module.params["port"]
    project_id = module.params["project_id"]
    url = f"{host}:{port}/api/project/{project_id}"

    try:
        headers = get_auth_headers(
            session_cookie=module.params.get("session_cookie"),
            api_token=module.params.get("api_token")
        )

        _, status, _ = semaphore_delete(url, headers=headers, validate_certs=module.params["validate_certs"])

        if status not in (200, 204):
            module.fail_json(msg=f"Failed to delete project: HTTP {status}", status=status)

        module.exit_json(changed=True, deleted=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
