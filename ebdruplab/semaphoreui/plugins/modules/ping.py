#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.semaphore_api import semaphore_get

DOCUMENTATION = r"""
---
module: ping
short_description: Check connection to Semaphore API
version_added: "1.0.0"
description:
  - Makes a GET request to the /ping endpoint of Semaphore API.
  - Optionally uses a session cookie for authentication.
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
  validate_certs:
    description:
      - Whether to validate SSL certificates.
    type: bool
    default: true
  session_cookie:
    description:
      - Optional session cookie from login response (e.g. `semaphore=<value>`).
    type: str
    required: false
author:
  - Kristian EBdrup (@kris9854)
"""

EXAMPLES = r"""
- name: Ping Semaphore
  ebdruplab.semaphoreui.ping:
    host: http://localhost
    port: 3000
  register: result

- name: Ping with authentication
  ebdruplab.semaphoreui.ping:
    host: https://semaphore.my.domain
    port: 443
    session_cookie: "semaphore=abc123"
    validate_certs: false
  register: result
"""

RETURN = r"""
pong:
  description: True if the server responded with 'pong'
  returned: always
  type: bool
  sample: true
"""

def main():
    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='int', required=True),
        validate_certs=dict(type='bool', default=True),
        session_cookie=dict(type='str', required=False, default=None)
    )

    result = dict(changed=False, pong=False)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    host = module.params['host'].rstrip('/')
    port = module.params['port']
    url = f"{host}:{port}/ping"
    validate_certs = module.params['validate_certs']
    session_cookie = module.params['session_cookie']

    headers = {}
    if session_cookie:
        headers['Cookie'] = session_cookie

    try:
        body = semaphore_get(url, validate_certs=validate_certs, headers=headers)
        if body.lower() == "pong":
            result['pong'] = True
            module.exit_json(**result)
        else:
            module.fail_json(msg=f"Unexpected response: {body}", **result)
    except Exception as e:
        module.fail_json(msg=str(e), **result)

if __name__ == '__main__':
    main()
