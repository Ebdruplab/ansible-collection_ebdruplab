#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_integration_create
short_description: Create a Semaphore project integration
version_added: "2.0.0"
description:
  - Creates an integration under a Semaphore project that triggers a template, optionally with auth and task params.
options:
  host:
    type: str
    required: true
  port:
    type: int
    required: true
  project_id:
    type: int
    required: true
  integration:
    type: dict
    required: true
    suboptions:
      name:
        type: str
        required: true
      template_id:
        type: int
        required: true
      auth_header:
        type: str
      auth_method:
        type: str
        choices: [token, basic, none]
      auth_secret_id:
        type: int
      task_params:
        type: dict
        suboptions:
          debug_level:
            type: int
          diff:
            type: bool
            default: false
          dry_run:
            type: bool
            default: false
  session_cookie:
    type: str
    required: false
    no_log: true
  api_token:
    type: str
    required: false
    no_log: true
  validate_certs:
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Create integration (token auth, with task params)
  ebdruplab.semaphoreui.project_integration_create:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 1
    integration:
      name: "Example Integration name"
      template_id: 1
      auth_method: token
      auth_header: "token"
      auth_secret_id: 3
      task_params:
        debug_level: 4
        diff: true
        dry_run: false
"""

RETURN = r"""
integration:
  type: dict
  returned: success
status:
  type: int
  returned: always
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            integration=dict(
                type="dict",
                required=True,
                options=dict(
                    name=dict(type="str", required=True),
                    template_id=dict(type="int", required=True),
                    auth_header=dict(type="str", required=False),
                    auth_method=dict(type="str", required=False, choices=["token", "basic", "none"]),
                    auth_secret_id=dict(type="int", required=False),
                    task_params=dict(
                        type="dict",
                        required=False,
                        options=dict(
                            debug_level=dict(type="int", required=False),
                            diff=dict(type="bool", required=False, default=False),
                            dry_run=dict(type="bool", required=False, default=False),
                        ),
                    ),
                ),
            ),
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
    integ = dict(module.params["integration"] or {})
    integ["project_id"] = project_id

    # Normalize task_params
    tp = integ.get("task_params") or {}
    norm_tp = {}
    if "debug_level" in tp and tp["debug_level"] is not None:
        try:
            norm_tp["debug_level"] = int(tp["debug_level"])
        except Exception:
            module.fail_json(msg="task_params.debug_level must be an integer")
    # Defaults for booleans
    norm_tp["diff"] = bool(tp.get("diff", False))
    norm_tp["dry_run"] = bool(tp.get("dry_run", False))
    if norm_tp:
        integ["task_params"] = norm_tp

    url = f"{host}:{port}/api/project/{project_id}/integrations"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers["Content-Type"] = "application/json"
    headers.setdefault("Accept", "application/json")

    try:
        body = json.dumps(integ).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url=url, body=body, headers=headers, validate_certs=validate_certs
        )

        if status not in (200, 201):
            text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else str(response_body)
            module.fail_json(msg=f"Failed to create integration: HTTP {status} - {text}", status=status)

        text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else response_body
        try:
            integration_obj = json.loads(text) if isinstance(text, str) else text
        except Exception:
            integration_obj = {"raw": text}

        module.exit_json(changed=True, integration=integration_obj, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
