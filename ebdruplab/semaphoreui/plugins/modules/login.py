#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post

import json

DOCUMENTATION = r'''
---
module: login
short_description: Log into Semaphore UI
description: Logs in and returns session cookie
options:
  host:
    type: str
    required: true
  port:
    type: int
    required: true
  username:
    type: str
    required: true
  password:
    type: str
    required: true
    no_log: true
  validate_certs:
    type: bool
    default: true
author:
  - Kristian Ebdrup @kris9854
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            username=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        supports_check_mode=False
    )

    url = f"{module.params['host']}:{module.params['port']}/api/auth/login"
    payload = {
        "auth": module.params["username"],
        "password": module.params["password"]
    }

    try:
        _, status, cookie = semaphore_post(url, body=payload, validate_certs=module.params["validate_certs"])
        if status != 204:
            module.fail_json(msg=f"Login failed, status: {status}")
        module.exit_json(changed=False, session_cookie=cookie)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
