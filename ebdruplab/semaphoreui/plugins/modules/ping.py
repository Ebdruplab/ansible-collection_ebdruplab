#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.semaphore_api import semaphore_get

DOCUMENTATION = r'''
---
module: ping
short_description: Ping the Semaphore API
description: Returns "pong" from the /ping endpoint
options:
  host:
    type: str
    required: true
  port:
    type: int
    required: true
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
            validate_certs=dict(type='bool', default=True)
        ),
        supports_check_mode=True
    )

    url = f"{module.params['host']}:{module.params['port']}/api/ping"

    try:
        response_body, status, _ = semaphore_get(url, validate_certs=module.params["validate_certs"])
        if status != 200 or response_body.lower() != "pong":
            module.fail_json(msg=f"Unexpected response: {response_body} (status {status})")
        module.exit_json(changed=False, result=response_body)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
