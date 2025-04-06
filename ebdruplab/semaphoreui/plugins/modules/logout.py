#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers

DOCUMENTATION = r'''
---
module: logout
short_description: Logout of Semaphore UI
description: Destroys the current session
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
  - Your Name
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True)
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    url = f"{module.params['host']}:{module.params['port']}/api/auth/logout"

    try:
        headers = get_auth_headers(module.params["session_cookie"], module.params["api_token"])
        _, status, _ = semaphore_post(url, headers=headers, validate_certs=module.params["validate_certs"])
        if status != 204:
            module.fail_json(msg=f"Logout failed, status: {status}")
        module.exit_json(changed=True)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
