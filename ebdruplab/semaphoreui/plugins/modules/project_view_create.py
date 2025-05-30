#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_view_create
short_description: Create a view in Semaphore
version_added: "1.0.0"
description:
  - Creates a new view within a Semaphore project.
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
      - ID of the project to associate the view with.
    type: int
    required: true
  title:
    description:
      - Title of the view.
    type: str
    required: true
  position:
    description:
      - Optional position of the view.
    type: int
    required: false
    default: 0
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
    required: false
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Create a view in Semaphore
  ebdruplab.semaphoreui.project_view_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    title: "My View"
    position: 1
"""

RETURN = r"""
view:
  description: The created view object.
  type: dict
  returned: success
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            title=dict(type="str", required=True),
            position=dict(type="int", required=False, default=0),
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
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/views"

    payload = {
        "title": module.params["title"],
        "project_id": project_id,
        "position": module.params["position"],
    }

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        body = json.dumps(payload).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status not in (200, 201):
            msg = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"Failed to create view: HTTP {status} - {msg}", status=status)

        result = json.loads(response_body.decode()) if isinstance(response_body, bytes) else json.loads(response_body)
        module.exit_json(changed=True, view=result)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

