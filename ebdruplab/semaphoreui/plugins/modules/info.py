#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: info
short_description: Fetch information about Semaphore
version_added: "1.0.0"
description:
  - Returns the current version and update info for the Semaphore server.
options:
  host:
    description:
      - The URL or IP address of the Semaphore server.
    required: true
    type: str
  port:
    description:
      - The port on which the Semaphore API is running.
    required: true
    type: int
  session_cookie:
    description:
      - Session cookie used for authentication.
    required: false
    type: str
    no_log: true
  api_token:
    description:
      - API token used for authentication.
    required: false
    type: str
    no_log: true
  validate_certs:
    description:
      - Whether to validate TLS certificates.
    required: false
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Get Semaphore info
  ebdruplab.semaphoreui.info:
    host: http://localhost
    port: 3000
    api_token: "abcd1234"
"""

RETURN = r"""
version:
  description: Information about the Semaphore server version.
  returned: success
  type: dict
  sample:
    build: "release"
    version: "2.9.48"
    update_available: false
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

    url = f"{module.params['host']}:{module.params['port']}/api/info"

    try:
        headers = get_auth_headers(
            module.params['session_cookie'],
            module.params['api_token']
        )
        response_body, status, _ = semaphore_get(url, headers=headers, validate_certs=module.params["validate_certs"])

        if status != 200:
            module.fail_json(msg=f"Failed to fetch info: HTTP {status} - {response_body}")

        info = json.loads(response_body)
        module.exit_json(changed=False, version=info)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

