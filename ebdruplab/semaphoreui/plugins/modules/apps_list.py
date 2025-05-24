#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers

DOCUMENTATION = r'''
---
module: apps_list
short_description: Get list of apps from Semaphore
description:
  - This module retrieves all apps defined in a Semaphore instance.
options:
  host:
    description:
      - The URL or IP of the Semaphore server.
    required: true
    type: str
  port:
    description:
      - The port on which Semaphore is running.
    required: true
    type: int
  session_cookie:
    description:
      - Session cookie for authenticating with Semaphore.
    required: false
    type: str
    no_log: true
  api_token:
    description:
      - API token for authenticating with Semaphore.
    required: false
    type: str
    no_log: true
  validate_certs:
    description:
      - Whether to validate TLS certificates.
    type: bool
    default: true
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Get apps from Semaphore
  ebdruplab.semaphoreui.apps_list:
    host: "http://localhost"
    port: 3000
    session_cookie: "{{ session_cookie }}"
  register: result

- name: Show app names
  debug:
    var: result.apps
'''

RETURN = r'''
apps:
  description: A list of app objects.
  returned: always
  type: list
  sample:
    - id: 1
      name: my-app
      git_url: https://github.com/example/repo.git
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
        supports_check_mode=False
    )

    host = module.params["host"]
    port = module.params["port"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/apps"
    headers = get_auth_headers(module.params["session_cookie"], module.params["api_token"])

    response_body, status, _ = semaphore_get(url, headers=headers, validate_certs=validate_certs)

    if status != 200:
        module.fail_json(msg=f"Failed to get apps: HTTP {status} - {response_body}")

    module.exit_json(changed=False, apps=response_body)

if __name__ == '__main__':
    main()
