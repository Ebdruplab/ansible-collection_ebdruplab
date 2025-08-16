#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_integration_matcher_update
short_description: Update a Semaphore integration matcher
version_added: "2.0.0"
description: Update an existing matcher on a project integration.
options:
  host:            {type: str, required: true}
  port:            {type: int, required: true}
  project_id:      {type: int, required: true}
  integration_id:  {type: int, required: true}
  matcher_id:      {type: int, required: true}
  matcher:
    description:
      - Fields to update. Some Semaphore installs require full object plus ids.
    type: dict
    required: true
    suboptions:
      name:           {type: str}
      match_type:     {type: str}
      method:         {type: str}
      body_data_type: {type: str}
      key:            {type: str}
      value:          {type: str}
  session_cookie:   {type: str, required: false, no_log: true}
  api_token:        {type: str, required: false, no_log: true}
  validate_certs:   {type: bool, default: true}
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Update a matcher
  ebdruplab.semaphoreui.project_integration_matcher_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    integration_id: 11
    matcher_id: 13
    matcher:
      name: "deploy"
      match_type: "body"
      method: "equals"
      body_data_type: "json"
      key: "action"
      value: "deploy"
"""

RETURN = r"""
matcher:
  description: Server response (if any) or the payload when HTTP 204.
  type: dict
status:
  description: HTTP status (204 expected).
  type: int
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            integration_id=dict(type="int", required=True),
            matcher_id=dict(type="int", required=True),
            matcher=dict(
                type="dict",
                required=True,
                options=dict(
                    name=dict(type="str"),
                    match_type=dict(type="str"),
                    method=dict(type="str"),
                    body_data_type=dict(type="str"),
                    key=dict(type="str"),
                    value=dict(type="str"),
                ),
            ),
            session_cookie=dict(type="str", no_log=True),
            api_token=dict(type="str", no_log=True),
            validate_certs=dict(type="bool", default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    integration_id = module.params["integration_id"]
    matcher_id = module.params["matcher_id"]
    validate_certs = module.params["validate_certs"]

    # Build payload; include identifiers to avoid 404s on some backends.
    body_fields = {k: v for k, v in (module.params["matcher"] or {}).items() if v is not None}
    if not body_fields:
        module.exit_json(changed=False, matcher={}, status=204)

    payload = {
        "id": matcher_id,
        "integration_id": integration_id,
        **body_fields,
    }

    url = f"{host}:{port}/api/project/{project_id}/integrations/{integration_id}/matchers/{matcher_id}"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers["Content-Type"] = "application/json"
    headers.setdefault("Accept", "application/json")

    try:
        body = json.dumps(payload).encode("utf-8")
        resp_body, status, _ = semaphore_put(url, body=body, headers=headers, validate_certs=validate_certs)

        if status == 204:
            module.exit_json(changed=True, matcher=payload, status=status)

        if status != 200:
            text = resp_body.decode() if isinstance(resp_body, (bytes, bytearray)) else str(resp_body)
            hint = ""
            if status == 404:
                hint = " (check project_id, integration_id, matcher_id, and that the matcher belongs to this integration)"
            module.fail_json(msg=f"PUT failed with status {status}: {text}{hint}", status=status)

        text = resp_body.decode() if isinstance(resp_body, (bytes, bytearray)) else resp_body
        try:
            matcher_obj = json.loads(text) if isinstance(text, str) else text
        except Exception:
            matcher_obj = {"raw": text}

        module.exit_json(changed=True, matcher=matcher_obj, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
