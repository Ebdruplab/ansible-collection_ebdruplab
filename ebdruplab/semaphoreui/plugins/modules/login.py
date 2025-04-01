#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.semaphore_api import semaphore_request
import json

DOCUMENTATION = r"""
---
module: login
short_description: Login to Semaphore UI and retrieve session cookie
version_added: "1.0.0"
description:
  - Logs into the Semaphore API using username and password.
  - Returns a session cookie to be reused in other modules.
options:
  host:
    description:
      - The host of the Semaphore API (e.g. http://localhost)
    required: true
    type: str
  port:
    description:
      - The port of the Semaphore API (e.g. 3000)
    required: true
    type: int
  username:
    description:
      - Semaphore login username
    required: true
    type: str
  password:
    description:
      - Semaphore login password
    required: true
    type: str
  validate_certs:
    description:
      - Whether to validate SSL certificates
    type: bool
    default: true
author:
  - Kristian Ebdrup (@kris9854)
"""

EXAMPLES = r"""
- name: Login to Semaphore
  ebdruplab.semaphoreui.login:
    host: http://localhost
    port: 3000
    username: admin
    password: secret
  register: login_result
"""

RETURN = r"""
cookie:
  description: Session cookie to use for authenticated requests
  returned: always
  type: str
  sample: semaphore=abc123
"""

def main():
    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='int', required=True),
        username=dict(type='str', required=True, no_log=True),
        password=dict(type='str', required=True, no_log=True),
        validate_certs=dict(type='bool', default=True)
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    url = f"{module.params['host'].rstrip('/')}:{module.params['port']}/auth/login"
    headers = {"Content-Type": "application/json"}
    body = {
        "auth": module.params["username"],
        "password": module.params["password"]
    }

    try:
        response_body, status, cookie = semaphore_request(
            method="POST",
            url=url,
            body=body,
            headers=headers,
            validate_certs=module.params["validate_certs"]
        )
        if cookie and "semaphore=" in cookie:
            module.exit_json(changed=False, cookie=cookie.split(";")[0])
        else:
            module.fail_json(msg="Login succeeded, but no session cookie received.")
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
