#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_integration_extraction_value_update
short_description: Update an extracted value for a Semaphore integration
version_added: "2.0.0"
description:
  - Updates a specific extracted value rule on a project integration in Semaphore.
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
  integration_id:
    type: int
    required: true
  extractvalue_id:
    type: int
    required: true
  value:
    type: dict
    required: true
    suboptions:
      name:
        type: str
      value_source:
        type: str
      body_data_type:
        type: str
      key:
        type: str
      variable:
        type: str
      variable_type:
        type: str
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
- name: Update an extracted value on an integration
  ebdruplab.semaphoreui.project_integration_extraction_value_update:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 1
    integration_id: 11
    extractvalue_id: 12
    value:
      name: "extract user id"
      value_source: "body"
      body_data_type: "json"
      key: "payload.user.id"
      variable: "USER_ID"
      variable_type: "environment"
"""

RETURN = r"""
extracted_value:
  description: The server response (if any), or the payload when status is 204.
  type: dict
  returned: success
status:
  description: HTTP status code (expected 204).
  type: int
  returned: always
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            integration_id=dict(type="int", required=True),
            extractvalue_id=dict(type="int", required=True),
            value=dict(
                type="dict",
                required=True,
                options=dict(
                    name=dict(type="str", required=False),
                    value_source=dict(type="str", required=False),
                    body_data_type=dict(type="str", required=False),
                    key=dict(type="str", required=False),
                    variable=dict(type="str", required=False),
                    variable_type=dict(type="str", required=False),
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
    integration_id = module.params["integration_id"]
    extractvalue_id = module.params["extractvalue_id"]
    validate_certs = module.params["validate_certs"]

    payload = dict(module.params["value"] or {})

    url = f"{host}:{port}/api/project/{project_id}/integrations/{integration_id}/values/{extractvalue_id}"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers["Content-Type"] = "application/json"
    headers.setdefault("Accept", "application/json")

    try:
        body = json.dumps(payload).encode("utf-8")
        response_body, status, _ = semaphore_put(
            url=url, body=body, headers=headers, validate_certs=validate_certs
        )

        if status == 204:
            module.exit_json(changed=True, extracted_value=payload, status=status)

        # Some servers may return 200 with the updated object
        if status == 200:
            text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else response_body
            try:
                obj = json.loads(text) if isinstance(text, str) else text
            except Exception:
                obj = {"raw": text}
            module.exit_json(changed=True, extracted_value=obj, status=status)

        text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else str(response_body)
        module.fail_json(msg=f"PUT failed with status {status}: {text}", status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
