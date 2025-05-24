#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers

DOCUMENTATION = r'''
---
module: project_key_get
short_description: Retrieve a specific SSH key from a Semaphore project
version_added: "1.0.0"
description:
  - Fetches details of a single SSH key resource within a specified Semaphore project.
options:
  host:
    description:
      - Hostname or IP (including protocol) of the Semaphore server.
    type: str
    required: true
  port:
    description:
      - Port number on which the Semaphore server is listening.
    type: int
    required: true
  project_id:
    description:
      - ID of the project containing the SSH key.
    type: int
    required: true
  key_id:
    description:
      - ID of the SSH key to retrieve.
    type: int
    required: true
  session_cookie:
    description:
      - Authentication cookie returned by the login module.
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - Bearer token for API authentication.
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - Whether to validate SSL certificates.
    type: bool
    default: true
'''

EXAMPLES = r'''
- name: Get a specific SSH key
  ebdruplab.semaphoreui.project_key_get:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    key_id: 42
  register: key_data

- name: Show SSH key
  debug:
    var: key_data.key
'''

RETURN = r'''
key:
  description: Details of the requested SSH key.
  type: dict
  returned: success
status:
  description: HTTP status code returned by the API.
  type: int
  returned: always
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            key_id=dict(type='int', required=True),
            session_cookie=dict(type='str', no_log=True),
            api_token=dict(type='str', no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[['session_cookie', 'api_token']],
        supports_check_mode=True
    )

    host = module.params['host'].rstrip('/')
    port = module.params['port']
    project_id = module.params['project_id']
    key_id = module.params['key_id']
    validate_certs = module.params['validate_certs']
    session_cookie = module.params.get('session_cookie')
    api_token = module.params.get('api_token')

    # Correct endpoint path: 'keys' not 'key'
    url = f"{host}:{port}/api/project/{project_id}/keys/{key_id}"

    try:
        headers = get_auth_headers(session_cookie=session_cookie, api_token=api_token)
        headers['Content-Type'] = 'application/json'

        response_body, status, _ = semaphore_get(
            url,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 200:
            module.fail_json(msg=f"Failed to retrieve SSH key: HTTP {status}", status=status)

        module.exit_json(changed=False, key=response_body, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

