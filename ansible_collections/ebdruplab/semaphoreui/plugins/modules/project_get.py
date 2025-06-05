#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_get
short_description: Fetch project details
version_added: "1.0.0"
description:
  - Retrieves a specific project's details by ID from Semaphore.
options:
  host:
    description:
      - Hostname or IP address of the Semaphore server (including protocol).
    required: true
    type: str
  port:
    description:
      - Port on which the Semaphore API is accessible.
    required: true
    type: int
  project_id:
    description:
      - ID of the Semaphore project to retrieve.
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
      - Bearer token for authentication.
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
- name: Get project by ID
  ebdruplab.semaphoreui.project_get:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
"""

RETURN = r"""
project:
  description: The project object returned by Semaphore.
  type: dict
  returned: always
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            session_cookie=dict(type="str", required=False, no_log=True),
            api_token=dict(type="str", required=False, no_log=True),
            validate_certs=dict(type="bool", default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers["Content-Type"] = "application/json"

    try:
        response_body, status, _ = semaphore_get(
            url, headers=headers, validate_certs=validate_certs
        )

        if status != 200:
            module.fail_json(
                msg=f"Failed to get project: HTTP {status}",
                response=response_body
            )

        project = json.loads(response_body)
        module.exit_json(changed=False, project=project)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()

