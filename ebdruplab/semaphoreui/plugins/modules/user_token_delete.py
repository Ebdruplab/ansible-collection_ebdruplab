#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r"""
---
module: user_token_delete
short_description: Delete an API token for the current Semaphore user
version_added: "1.0.0"
description:
  - Deletes a specific API token by ID for the currently authenticated user in Semaphore.
options:
  host:
    description:
      - Hostname or IP address of the Semaphore server (e.g., http://localhost).
    type: str
    required: true
  port:
    description:
      - Port number on which the Semaphore API is accessible.
    type: int
    required: true
  api_token_id:
    description:
      - ID of the API token to delete.
    type: str
    required: true
  session_cookie:
    description:
      - Session cookie returned by the login module.
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - API token used for authentication instead of session cookie.
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - Whether to validate TLS/SSL certificates.
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Delete a user API token
  ebdruplab.semaphoreui.user_token_delete:
    host: http://localhost
    port: 3000
    api_token: "{{ login_result.api_token }}"
    api_token_id: "42"
"""

RETURN = r"""
deleted:
  description: Whether the token was successfully deleted.
  type: bool
  returned: always
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            api_token_id=dict(type='str', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True)
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    url = f"{module.params['host']}:{module.params['port']}/api/user/tokens/{module.params['api_token_id']}"
    headers = get_auth_headers(module.params['session_cookie'], module.params['api_token'])

    try:
        _, status, _ = semaphore_delete(url, headers=headers, validate_certs=module.params["validate_certs"])
        if status != 204:
            module.fail_json(msg=f"Failed to delete token: HTTP {status}")
        module.exit_json(changed=True, deleted=True)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

