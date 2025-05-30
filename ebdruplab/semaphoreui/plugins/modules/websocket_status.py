#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers

DOCUMENTATION = r'''
---
module: websocket_status
short_description: Check WebSocket support on the Semaphore server
version_added: "1.0.0"
description:
  - Sends a GET request to the /ws endpoint to determine if WebSocket is reachable.
  - Authentication is required as of Semaphore 2.x and above.
options:
  host:
    description: Hostname or IP address (with protocol) of the Semaphore server.
    type: str
    required: true
  port:
    description: Port number where the Semaphore API is exposed.
    type: int
    required: true
  session_cookie:
    description: Session authentication cookie.
    type: str
    required: false
    no_log: true
  api_token:
    description: API token for authentication.
    type: str
    required: false
    no_log: true
  validate_certs:
    description: Whether to validate SSL/TLS certificates.
    type: bool
    default: true
author:
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: Check WebSocket endpoint
  ebdruplab.semaphoreui.websocket_status:
    host: http://localhost
    port: 3000
    api_token: "abcd1234"
'''

RETURN = r'''
reachable:
  description: Whether the /ws endpoint responded with HTTP 200 OK.
  type: bool
  returned: always
status:
  description: HTTP status code from the GET request to /ws.
  type: int
  returned: always
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
        supports_check_mode=True
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/ws"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        _, status, _ = semaphore_get(
            url, headers=headers, validate_certs=validate_certs
        )

        module.exit_json(changed=False, reachable=(status == 200), status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

