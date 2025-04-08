from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: user_get
short_description: Fetch details of the logged-in user
description: Retrieves information about the currently authenticated user.
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
author: Kristian Ebdrup @kris9854
"""

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

    url = f"{module.params['host']}:{module.params['port']}/api/user"
    headers = get_auth_headers(module.params['session_cookie'], module.params['api_token'])

    try:
        response_body, status, _ = semaphore_get(url, headers=headers, validate_certs=module.params["validate_certs"])
        if status != 200:
            module.fail_json(msg=f"Failed to get user: HTTP {status} - {response_body}")
        module.exit_json(changed=False, user=json.loads(response_body))
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()