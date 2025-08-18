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
    description:
      - Base URL of the Semaphore server, including scheme (e.g. C(http://localhost)).
    type: str
    required: true
  port:
    description:
      - Port where the Semaphore API is exposed.
    type: int
    required: true
  project_id:
    description:
      - ID of the project that owns the integration.
    type: int
    required: true
  integration_id:
    description:
      - ID of the integration that contains the extracted value rule.
    type: int
    required: true
  extractvalue_id:
    description:
      - ID of the extracted value to update.
    type: int
    required: true
  value:
    description:
      - Fields to update on the extracted value. Provide one or more.
    type: dict
    required: true
    suboptions:
      name:
        description:
          - Human-readable name for the extracted value rule.
        type: str
      value_source:
        description:
          - Location of the value to extract (for example C(body), C(headers), or C(query)).
        type: str
      body_data_type:
        description:
          - Data type when reading from the request body (for example C(json) or C(text)).
        type: str
      key:
        description:
          - Path or key selector used to find the value (e.g. C(payload.user.id)).
        type: str
      variable:
        description:
          - Variable name to store the extracted value as (e.g. C(USER_ID)).
        type: str
      variable_type:
        description:
          - Target bucket for the variable (for example C(environment) or C(json)).
        type: str
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
      - Validate TLS certificates when using HTTPS.
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
  description:
    - Server response (if any) or the update payload when the API returns C(204 No Content).
  type: dict
  returned: success
status:
  description:
    - HTTP status code (C(204) expected on success).
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
