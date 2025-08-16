#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_integration_delete
short_description: Delete a Semaphore project integration
version_added: "2.0.0"
description:
  - Removes an integration from a Semaphore project.
options:
  host:
    type: str
    required: true
  port:
    type: int
    required: true
  project_id:
    type: int
    required: true
  integration_id:
    type: int
    required: true
  session_cookie:
    type: str
    required: false
    no_log: true
  api_token:
    type: str
    required: false
    no_log: true
  validate_certs:
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Delete integration (session)
  ebdruplab.semaphoreui.project_integration_delete:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    integration_id: 11

- name: Delete integration (token)
  ebdruplab.semaphoreui.project_integration_delete:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 1
    integration_id: 11
"""

RETURN = r"""
status:
  description: HTTP status code (204 on success).
  type: int
  returned: always
detail:
  description: Raw server response (if any).
  type: str
  returned: sometimes
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            integration_id=dict(type="int", required=True),
            session_cookie=dict(type="str", required=False, no_log=True),
            api_token=dict(type="str", required=False, no_log=True),
            validate_certs=dict(type="bool", default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    integration_id = module.params["integration_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/integrations/{integration_id}"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers.setdefault("Accept", "application/json")

    try:
        response_body, status, _ = semaphore_delete(
            url=url,
            headers=headers,
            validate_certs=validate_certs,
        )

        if status in (200, 204):
            detail = (
                response_body.decode()
                if isinstance(response_body, (bytes, bytearray))
                else (response_body if isinstance(response_body, str) else "")
            )
            module.exit_json(changed=True, status=status, detail=detail)

        text = (
            response_body.decode()
            if isinstance(response_body, (bytes, bytearray))
            else str(response_body)
        )
        module.fail_json(msg=f"Failed to delete integration: HTTP {status} - {text}", status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
