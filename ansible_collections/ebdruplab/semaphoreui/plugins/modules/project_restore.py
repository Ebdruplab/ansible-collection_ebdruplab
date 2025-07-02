#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_request, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_restore
short_description: Restore a Semaphore project
version_added: "1.0.0"
description:
  - Restores a Semaphore project from backup data using the /api/projects/restore endpoint.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (with http or https).
    type: str
    required: true
  port:
    description:
      - Port on which the Semaphore server is running.
    type: int
    required: true
  backup:
    description:
      - Backup dictionary representing a previously exported Semaphore project.
    type: dict
    required: true
  session_cookie:
    description:
      - Session cookie for authentication.
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - API token for authentication.
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - Whether to validate TLS certificates.
    type: bool
    default: true
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Restore Semaphore project from backup
  ebdruplab.semaphoreui.project_restore:
    host: http://localhost
    port: 3000
    api_token: "abcd1234"
    backup: "{{ lookup('file', 'project_backup.json') | from_json }}"
'''

RETURN = r'''
project:
  description: Restored project information
  type: dict
  returned: success
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            backup=dict(type='dict', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    backup_data = module.params["backup"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/projects/restore"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        body = json.dumps(backup_data).encode("utf-8")

        response_body, status, _ = semaphore_request(
            "POST", url, body=body, headers=headers, validate_certs=validate_certs
        )

        if status != 200:
            error_msg = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"Failed to restore project: HTTP {status} - {error_msg}", status=status)

        result = json.loads(response_body)
        module.exit_json(changed=True, project=result)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

