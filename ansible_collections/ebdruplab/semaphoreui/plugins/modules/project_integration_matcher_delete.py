#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r"""
---
module: project_integration_matcher_delete
short_description: Delete a Semaphore integration matcher
version_added: "2.0.0"
description: Removes a matcher from a project integration.
options:
  host:          {type: str, required: true}
  port:          {type: int, required: true}
  project_id:    {type: int, required: true}
  integration_id:{type: int, required: true}
  matcher_id:    {type: int, required: true}
  session_cookie:{type: str, required: false, no_log: true}
  api_token:     {type: str, required: false, no_log: true}
  validate_certs:{type: bool, default: true}
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Delete an integration matcher
  ebdruplab.semaphoreui.project_integration_matcher_delete:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 1
    integration_id: 11
    matcher_id: 13
"""

RETURN = r"""
status:
  description: HTTP status (204 on success).
  type: int
  returned: always
changed:
  description: Whether the matcher was removed.
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
            matcher_id=dict(type="int", required=True),
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
    matcher_id = module.params["matcher_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/integrations/{integration_id}/matchers/{matcher_id}"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )

    try:
        resp_body, status, _ = semaphore_delete(url, headers=headers, validate_certs=validate_certs)

        if status == 204:
            module.exit_json(changed=True, status=status)

        # Some servers may return 200 with a body
        if status == 200:
            module.exit_json(changed=True, status=status)

        msg = resp_body.decode() if isinstance(resp_body, (bytes, bytearray)) else str(resp_body)
        module.fail_json(msg=f"DELETE failed with status {status}: {msg}", status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
