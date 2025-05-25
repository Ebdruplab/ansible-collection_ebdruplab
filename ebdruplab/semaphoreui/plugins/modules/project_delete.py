#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r"""
---
module: project_delete
short_description: Delete a Semaphore project
version_added: "1.0.0"
description:
  - Deletes a project from the Semaphore server using the project ID.
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
  project_id:
    description:
      - ID of the project to delete.
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
- name: Delete a Semaphore project
  ebdruplab.semaphoreui.project_delete:
    host: http://localhost
    port: 3000
    api_token: "your_api_token"
    project_id: 1

- name: Delete a project using session cookie
  ebdruplab.semaphoreui.project_delete:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 2
"""

RETURN = r"""
deleted:
  description: Whether the project was successfully deleted.
  type: bool
  returned: always
  sample: true

status:
  description: HTTP response code from the server.
  type: int
  returned: always
  sample: 204
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params["host"]
    port = module.params["port"]
    project_id = module.params["project_id"]
    url = f"{host}:{port}/api/project/{project_id}"

    try:
        headers = get_auth_headers(
            session_cookie=module.params.get("session_cookie"),
            api_token=module.params.get("api_token")
        )

        _, status, _ = semaphore_delete(url, headers=headers, validate_certs=module.params["validate_certs"])

        if status not in (200, 204):
            module.fail_json(msg=f"Failed to delete project: HTTP {status}", status=status)

        module.exit_json(changed=True, deleted=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

