#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_backup
short_description: Backup a Semaphore project
version_added: "1.0.0"
description:
  - Fetches a complete backup of a Semaphore project by project ID.
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
      - ID of the project to back up.
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
- name: Backup Semaphore project
  ebdruplab.semaphoreui.project_backup:
    host: http://localhost
    port: 3000
    project_id: 1
    api_token: "abcd1234"
  register: project_backup

- name: Show backup data
  debug:
    var: project_backup.backup
"""

RETURN = r"""
backup:
  description: Backup data of the specified Semaphore project.
  returned: success
  type: dict
  sample:
    project:
      id: 1
      name: MyProject
    templates:
      - id: 10
        name: deploy
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

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/backup"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        response_body, status, _ = semaphore_get(url, headers=headers, validate_certs=validate_certs)

        if status != 200:
            module.fail_json(msg=f"Failed to backup project: HTTP {status}", response=response_body)

        backup_data = json.loads(response_body)
        module.exit_json(changed=False, backup=backup_data)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

