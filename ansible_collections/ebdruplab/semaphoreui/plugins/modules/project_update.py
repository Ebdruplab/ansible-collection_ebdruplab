#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_update
short_description: Update a Semaphore project
version_added: "1.0.0"
description:
  - Updates metadata for an existing Semaphore project by ID.
options:
  host:
    description:
      - Hostname or IP address of the Semaphore server (e.g., http://localhost).
    type: str
    required: true
  port:
    description:
      - Port where Semaphore API is listening (e.g., 3000).
    type: int
    required: true
  project_id:
    description:
      - ID of the project to update.
    type: int
    required: true
  project:
    description:
      - Dictionary defining updated project fields.
    type: dict
    required: true
  session_cookie:
    description:
      - Session cookie from login module.
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - API token used for authentication.
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - Whether to validate SSL certificates.
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Update Semaphore project
  ebdruplab.semaphoreui.project_update:
    host: http://localhost
    port: 3000
    api_token: "abcd1234"
    project_id: 1
    project:
      name: "Updated Project"
      alert: true
      alert_chat: "Slack"
      max_parallel_tasks: 2
      type: "test"
      demo: false
"""

RETURN = r"""
updated:
  description: Whether the project was successfully updated.
  type: bool
  returned: always
status:
  description: HTTP response code.
  type: int
  returned: always
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            project=dict(type='dict', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params['host']
    port = module.params['port']
    project_id = module.params['project_id']
    project_data = module.params['project']
    validate_certs = module.params['validate_certs']

    url = f"{host}:{port}/api/project/{project_id}"

    try:
        headers = get_auth_headers(
            session_cookie=module.params.get("session_cookie"),
            api_token=module.params.get("api_token")
        )
        project_data["id"] = project_id  # Ensure ID is included in body
        body = json.dumps(project_data).encode("utf-8")

        _, status, _ = semaphore_put(
            url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 204:
            module.fail_json(msg=f"Failed to update project: HTTP {status}", status=status)

        module.exit_json(changed=True, updated=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

