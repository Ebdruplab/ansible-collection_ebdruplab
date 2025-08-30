#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_template_list
short_description: List templates in a Semaphore project
version_added: "1.0.0"
description:
  - Retrieves a list of templates from a specific Semaphore project.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (including protocol).
    type: str
    required: true
  port:
    description:
      - Port on which the Semaphore server is listening.
    type: int
    required: true
  project_id:
    description:
      - ID of the project to list templates for.
    type: int
    required: true
  session_cookie:
    description:
      - Session cookie for authentication (obtained from login module).
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
      - Whether to validate SSL certificates.
    type: bool
    default: true
  sort:
    description:
      - Field to sort by (e.g., C(name), C(type), etc.).
    type: str
    required: false
  order:
    description:
      - Sort order (ascending or descending).
    type: str
    required: false
    choices: ["asc", "desc"]
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: List templates in a project (sorted by name ascending)
  ebdruplab.semaphoreui.project_template_list:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    sort: name
    order: asc
"""

RETURN = r"""
templates:
  description: List of templates in the specified project.
  type: list
  elements: dict
  returned: success
status:
  description: HTTP status code from the Semaphore API
  type: int
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
            sort=dict(type="str", required=False),
            order=dict(type="str", required=False, choices=["asc", "desc"]),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/templates"
    q = []
    if module.params.get("sort"):
        q.append(f"sort={module.params['sort']}")
    if module.params.get("order"):
        q.append(f"order={module.params['order']}")
    if q:
        url += "?" + "&".join(q)

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers.setdefault("Accept", "application/json")

    try:
        resp_body, status, _ = semaphore_get(
            url, headers=headers, validate_certs=validate_certs
        )

        if status != 200:
            text = resp_body.decode() if isinstance(resp_body, (bytes, bytearray)) else str(resp_body)
            module.fail_json(msg=f"GET failed with status {status}: {text}", status=status)

        # Robust JSON normalization
        if isinstance(resp_body, (bytes, bytearray)):
            text = resp_body.decode()
            try:
                templates = json.loads(text)
            except Exception:
                templates = []
        elif isinstance(resp_body, str):
            try:
                templates = json.loads(resp_body)
            except Exception:
                templates = []
        else:
            templates = resp_body if isinstance(resp_body, list) else []

        module.exit_json(changed=False, templates=templates, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
