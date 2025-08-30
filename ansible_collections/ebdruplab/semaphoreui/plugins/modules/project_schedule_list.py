#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
from urllib.parse import urlencode

import json

DOCUMENTATION = r"""
---
module: project_schedule_list
short_description: List Semaphore project schedules
version_added: "2.0.2"
description:
  - Returns all schedules for a given project via C(GET /api/project/{project_id}/schedules).
  - Optional C(sort) and C(order) query parameters are passed through to the API if provided.
options:
  host:
    description:
      - Base URL of the Semaphore server including scheme (e.g. C(http://localhost)).
    type: str
    required: true
  port:
    description:
      - Port where the Semaphore API is exposed (e.g. C(3000)).
    type: int
    required: true
  project_id:
    description:
      - ID of the project to list schedules for.
    type: int
    required: true
  sort:
    description:
      - Optional sort field supported by the API (e.g. C(name)).
    type: str
    required: false
  order:
    description:
      - Optional order direction.
    type: str
    required: false
    choices: ["asc", "desc"]
  session_cookie:
    description:
      - Session cookie for authentication. Use this or C(api_token).
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - Bearer token for authentication. Use this or C(session_cookie).
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - Whether to validate TLS certificates when using HTTPS.
    type: bool
    default: true

author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: List schedules for a project (token)
  ebdruplab.semaphoreui.project_schedule_list:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 1
  register: schedules_result

- name: List schedules for a project (session) sorted by name
  ebdruplab.semaphoreui.project_schedule_list:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    sort: name
    order: asc
  register: schedules_result
"""

RETURN = r"""
schedules:
  description:
    - List of schedule objects.
  type: list
  returned: success
status:
  description:
    - HTTP status code (C(200) on success).
  type: int
  returned: always
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            sort=dict(type="str", required=False),
            order=dict(type="str", required=False, choices=["asc", "desc"]),
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

    base_url = f"{host}:{port}/api/project/{project_id}/schedules"

    q = {}
    if module.params.get("sort"):
        q["sort"] = module.params["sort"]
    if module.params.get("order"):
        q["order"] = module.params["order"]
    url = f"{base_url}?{urlencode(q)}" if q else base_url

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers.setdefault("Accept", "application/json")

    try:
        resp_body, status, _ = semaphore_get(url, headers=headers, validate_certs=validate_certs)

        if status != 200:
            text = resp_body.decode() if isinstance(resp_body, (bytes, bytearray)) else str(resp_body)
            module.fail_json(msg=f"GET failed with status {status}: {text}", status=status)

        # Normalize JSON body
        if isinstance(resp_body, (bytes, bytearray)):
            text = resp_body.decode()
            try:
                schedules = json.loads(text)
            except Exception:
                schedules = []
        elif isinstance(resp_body, str):
            try:
                schedules = json.loads(resp_body)
            except Exception:
                schedules = []
        else:
            schedules = resp_body

        module.exit_json(changed=False, schedules=schedules, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
