#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_view_get
short_description: Get a specific view from a Semaphore project
version_added: "1.0.0"
description:
  - Retrieves a view object by its ID within a given project in Semaphore.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (excluding protocol).
    type: str
    required: true
  port:
    description:
      - Port of the Semaphore server (e.g., 3000).
    type: int
    required: true
  project_id:
    description:
      - ID of the project containing the view.
    type: int
    required: true
  view_id:
    description:
      - ID of the view to retrieve.
    type: int
    required: true
  session_cookie:
    description:
      - Session cookie used for authentication.
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
      - Whether to validate TLS certificates.
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Get a view from a project
  ebdruplab.semaphoreui.project_view_get:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    view_id: 10
"""

RETURN = r"""
view:
  description: The view object retrieved from the project.
  type: dict
  returned: success
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            view_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    view_id = module.params["view_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/views/{view_id}"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )

    try:
        response_body, status, _ = semaphore_get(
            url=url,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 200:
            module.fail_json(msg=f"Failed to get view: HTTP {status}", status=status)

        result = json.loads(response_body.decode()) if isinstance(response_body, bytes) else json.loads(response_body)
        module.exit_json(changed=False, view=result)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

