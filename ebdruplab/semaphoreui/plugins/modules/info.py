# plugins/modules/info.py

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: info
short_description: Fetches information about Semaphore
version_added: "1.0.0"
description:
  - Returns current version and update info for the Semaphore server
options:
  host:
    type: str
    required: true
  port:
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
- name: Get Semaphore info
  ebdruplab.semaphoreui.info:
    host: http://localhost
    port: 3000
    api_token: "abcd1234"
'''

RETURN = r'''
version:
  description: Semaphore version info
  returned: always
  type: dict
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    url = f"{module.params['host']}:{module.params['port']}/api/info"

    try:
        headers = get_auth_headers(
            module.params['session_cookie'],
            module.params['api_token']
        )
        response_body, status, _ = semaphore_get(url, headers=headers, validate_certs=module.params["validate_certs"])

        if status != 200:
            module.fail_json(msg=f"Failed to fetch info: HTTP {status} - {response_body}")

        info = json.loads(response_body)
        module.exit_json(changed=False, version=info)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

