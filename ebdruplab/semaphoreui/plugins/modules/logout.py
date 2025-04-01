#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.semaphore_api import semaphore_request

DOCUMENTATION = r"""
---
module: logout
short_description: Logout from Semaphore UI
version_added: "1.0.0"
description:
  - Logs out from the Semaphore API using the session cookie.
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
  session_cookie:
    description:
      - Session cookie obtained from login module (e.g. semaphore=abc123)
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
- name: Logout from Semaphore
  ebdruplab.semaphoreui.logout:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.cookie }}"
"""

RETURN = r"""
logged_out:
  description: Whether the logout succeeded
  returned: always
  type: bool
  sample: true
"""

def main():
    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='int', required=True),
        session_cookie=dict(type='str', required=True),
        validate_certs=dict(type='bool', default=True)
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    url = f"{module.params['host'].rstrip('/')}:{module.params['port']}/auth/logout"
    headers = {
        "Content-Type": "application/json",
        "Cookie": module.params['session_cookie']
    }

    try:
        _, status, _ = semaphore_request(
            method="POST",
            url=url,
            headers=headers,
            validate_certs=module.params["validate_certs"]
        )
        module.exit_json(changed=False, logged_out=status in (200, 204))
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
