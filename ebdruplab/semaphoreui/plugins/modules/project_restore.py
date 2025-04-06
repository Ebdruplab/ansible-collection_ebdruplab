# plugins/modules/project_restore.py

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_request, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_restore
short_description: Restore a Semaphore project
version_added: "1.0.0"
description:
  - Restores a Semaphore project from backup data
options:
  host:
    type: str
    required: true
  port:
    type: int
    required: true
  backup:
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
  - Kristian Ebdrup @kris9854
"""

EXAMPLES = r"""
- name: Restore Semaphore project
  ebdruplab.semaphoreui.project_restore:
    host: http://localhost
    port: 3000
    api_token: "abcd1234"
    backup: "{{ lookup('file', 'project_backup.json') | from_json }}"
"""

RETURN = r"""
project:
  description: Restored project information
  returned: always
  type: dict
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            backup=dict(type='dict', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    url = f"{module.params['host']}:{module.params['port']}/api/projects/restore"

    try:
        headers = get_auth_headers(module.params["session_cookie"], module.params["api_token"])
        response_body, status, _ = semaphore_request("POST", url, body=module.params["backup"], headers=headers, validate_certs=module.params["validate_certs"])
        if status != 200:
            module.fail_json(msg=f"Failed to restore project: HTTP {status} - {response_body}")
        data = json.loads(response_body)
        module.exit_json(changed=True, project=data)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
