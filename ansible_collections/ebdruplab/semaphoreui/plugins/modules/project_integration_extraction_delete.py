#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r"""
---
module: project_integration_extraction_delete
short_description: Delete an extracted value from a Semaphore integration
version_added: "2.0.0"
description:
  - Removes a specific extracted value rule from a project integration.
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
  extractvalue_id:
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
- name: Delete extraction value (session)
  ebdruplab.semaphoreui.project_integration_extraction_delete:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    integration_id: 11
    extractvalue_id: 12

- name: Delete extraction value (token)
  ebdruplab.semaphoreui.project_integration_extraction_delete:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 1
    integration_id: 11
    extractvalue_id: 12
"""

RETURN = r"""
status:
  description: HTTP status code (204 on success).
  type: int
  returned: always
changed:
  description: Whether a deletion occurred.
  type: bool
  returned: always
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            integration_id=dict(type="int", required=True),
            extractvalue_id=dict(type="int", required=True),
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
    extractvalue_id = module.params["extractvalue_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/integrations/{integration_id}/values/{extractvalue_id}"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )

    try:
        _, status, _ = semaphore_delete(
            url=url, headers=headers, validate_certs=validate_certs
        )

        if status in (200, 204):
            module.exit_json(changed=True, status=status)

        module.fail_json(msg=f"DELETE failed with status {status}", status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
