from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_backup
short_description: Backup a Semaphore project
version_added: "1.0.0"
description:
  - Fetches a complete backup of a Semaphore project by project ID.
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
- name: Backup Semaphore project
  ebdruplab.semaphoreui.project_backup:
    host: http://localhost
    port: 3000
    project_id: 1
    api_token: "abcd1234"
'''

RETURN = r'''
backup:
  description: Backup data of the project
  returned: always
  type: dict
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

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/backup"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        response_body, status, _ = semaphore_get(url, headers=headers, validate_certs=validate_certs)

        if status != 200:
            module.fail_json(msg=f"Failed to backup project: HTTP {status}", response=response_body)

        backup_data = json.loads(response_body)
        module.exit_json(changed=False, backup=backup_data)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

